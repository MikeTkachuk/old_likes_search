// Init state
let allTweets = {}; // map: id → { id, filenames: [...], metadata: {...} }
let idSequence = [];
const BATCH_SIZE = 20;
let nextIndex = 0;

// Setup observer on the anchor
const observer = new IntersectionObserver(onIntersect, {
    root: null, rootMargin: '0px', threshold: 0.1
});
const anchor = document.getElementById('scroll-anchor');
function observe(){
    observer.observe(anchor);
}
function unobserve(){
    observer.unobserve(anchor);
}
let renderLock = 0;
const [listResp, metaResp] = await Promise.all([fetch("tweets_list_cache.txt"), fetch("tweets_metadata_cache.txt")]);
if (!listResp.ok || !metaResp.ok) {
    throw new Error('Failed to fetch files');
}
const [listText, metaText] = await Promise.all([listResp.text(), metaResp.text()]);
parseListing(listText);
parseJsonLines(metaText);
updateSequence();

// Run once DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', resetView);
} else {
    resetView();
}


// Parse text listing file: skip JSON filenames
function parseListing(txt) {
    const lines = txt.split(/\r?\n/);
    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        const [group, ...files] = trimmed.split(/\s+/);
        if (!group) continue;
        const filenames = files.filter(name => !name.endsWith('.json'));
        allTweets[group] = {
            id: group, filenames, metadata: null
        };
    }
}


// Parse a JSONL file: each line a JSON object with id & meta
function parseJsonLines(txt) {
    const lines = txt.split(/\r?\n/);
    for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        try {
            const obj = JSON.parse(trimmed);
            const id = String(obj.id);
            if (allTweets[id]) {
                allTweets[id].metadata = obj;
            } else {
                // Optionally include unmatched metadata
                allTweets[id] = {id, filenames: [], metadata: obj};
            }
        } catch (err) {
            console.warn('Skipping bad JSON line:', trimmed);
        }
    }
}


// Main sequence generator
export function updateSequence() {
    idSequence = [];
    let tweets = Object.values(allTweets);
    const term = document.getElementById('search_box').value.trim().toLowerCase();
    const isReverse = document.getElementById('reverse-toggle').checked;
    const allMediaTypes = ['photo', 'video'];
    let mediaTypes = [];
    let mediaTypeOther = document.getElementById('include_other').checked;
    if (document.getElementById('include_photo').checked) {
        mediaTypes.push('photo');
    }
    if (document.getElementById('include_video').checked) {
        mediaTypes.push('video');
    }

    idSequence = tweets.filter(obj => {
        const textMatch = !term || (obj.metadata?.text.toLowerCase().includes(term) ?? false);

        const typeMatch = obj.metadata?.media_urls?.some(([, type]) => mediaTypes.includes(type) || (!allMediaTypes.includes(type) && mediaTypeOther)) ?? false;

        return textMatch && typeMatch;
    }).map(tweet => tweet.id);
    idSequence.sort((a, b) => {
        const idA = BigInt(a);
        const idB = BigInt(b);
        return isReverse ? Number(idB - idA) : Number(idA - idB);
    });
}


// Render the next batch of items into gallery
async function renderBatch() {
    if (renderLock === 1){
        return;
    }
    else{
        renderLock = 1;
    }
    unobserve();
    const tweets_div = document.getElementById('tweets_div');
    const slice = idSequence.slice(nextIndex, nextIndex + BATCH_SIZE);
    for (const s of slice) {
        console.log(s)
        let el = createTweetBlock(allTweets[s].metadata);
        tweets_div.appendChild(el);
        await wait(100);
    }
    nextIndex += slice.length;
    if (nextIndex < idSequence.length) {
        observe();
    } else {
        console.log("reached end, disconnecting observer...");
    }
    renderLock = 0;
}

// IntersectionObserver callback
function onIntersect(entries) {
    console.log("triggered onIntersect");
    entries.forEach(entry => {
        if (entry.isIntersecting && nextIndex < idSequence.length) {
            renderBatch().then(() => {
            });
        }
    });
}


// Initialize gallery and observer
export function resetView() {
    if (renderLock === 1){
        return;
    }
    const tweets_div = document.getElementById('tweets_div');
    tweets_div.innerHTML = '';

    nextIndex = 0;
    renderBatch().then(() => {
    });
}

// Renderer
function loadWithRetry(el, maxRetries = 3) {
    let attempts = 0;

    return new Promise(resolve => {
        function tryLoad() {
            attempts++;
            el.src = el.src.split('?')[0] + '?v=' + Math.random();

            const onSuccess = () => {
                cleanup();
                resolve();
            };
            const onError = () => {
                cleanup();
                if (attempts <= maxRetries) {
                    setTimeout(tryLoad, 1000); // retry after 1s
                } else {
                    console.warn('Failed to load after retry:', el.src);
                    resolve();
                }
            };

            el.addEventListener('load', onSuccess, {once: true});
            el.addEventListener('loadeddata', onSuccess, {once: true});
            el.addEventListener('error', onError, {once: true});

            function cleanup() {
                el.removeEventListener('load', onSuccess);
                el.removeEventListener('loadeddata', onSuccess);
                el.removeEventListener('error', onError);
            }
        }

        tryLoad();
    });
}

function wait(ms) {
    return new Promise(res => setTimeout(res, ms));
}

function createTweetBlock(tweet_meta) {
    const container = document.createElement('div');
    container.id = String(tweet_meta.id);
    container.className = 'tweet';

    const contentDiv = document.createElement('div');

    const textEl = document.createElement('text');
    textEl.textContent = tweet_meta.text;
    contentDiv.appendChild(textEl);

    const linkEl = document.createElement('a');
    linkEl.href = tweet_meta.link;
    linkEl.target = "_blank";
    linkEl.textContent = '[link]';
    contentDiv.appendChild(linkEl);

    container.appendChild(contentDiv);

    const mediaContainer = document.createElement('div');
    for (let i = 0; i < tweet_meta.media_urls.length; i++) {
        const [rawUrl, type] = tweet_meta.media_urls[i];
        const extension = rawUrl.split('.').pop();
        const mediaUrl = `tweets/${tweet_meta.id}/${i}.${extension}`;

        let mediaEl;
        if (type === 'video') {
            mediaEl = document.createElement('video');
            mediaEl.className = 'vid';
            mediaEl.src = mediaUrl;
            mediaEl.loading = 'lazy';
            mediaEl.controls = true;
            mediaEl.autoplay = false;
        } else if (type === 'photo') {
            mediaEl = document.createElement('img');
            mediaEl.className = 'image';
            mediaEl.src = mediaUrl;
            mediaEl.loading = 'lazy';
            addFullScreenCallback(mediaEl);
        } else {
            mediaEl = document.createElement('video');
            mediaEl.className = 'gif';
            mediaEl.src = mediaUrl;
            mediaEl.autoplay = true;
            mediaEl.loop = true;
            mediaEl.muted = true;
            mediaEl.playsInline = true;
            mediaEl.loading = 'lazy';
            // addFullScreenCallback(mediaEl);  // todo
        }
        loadWithRetry(mediaEl);
        mediaContainer.appendChild(mediaEl);
    }
    container.appendChild(mediaContainer);

    const hr = document.createElement('hr');
    container.appendChild(hr);

    return container;
}


// Buttons

export function topFunction() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}

export function pauseAll() {
    document.querySelectorAll('video').forEach(vid => vid.pause());
    document.querySelectorAll('.vid').forEach(i => i.contentWindow.document.querySelectorAll('video').forEach(vid => vid.pause()));
}

function scrollTo() {
    // todo
    const val = document.getElementById("navigate_param").value;
    let tweets = document.querySelectorAll(".tweet");
    tweets[Math.floor(val / 100 * tweets.length)].scrollIntoView();
}

function shuffle(array) {
    let currentIndex = array.length, randomIndex;

    // While there remain elements to shuffle.
    while (currentIndex !== 0) {

        // Pick a remaining element.
        randomIndex = Math.floor(Math.random() * currentIndex);
        currentIndex--;

        // And swap it with the current element.
        [array[currentIndex], array[randomIndex]] = [array[randomIndex], array[currentIndex]];
    }

    return array;
}

export function shuffleSequence() {
    shuffle(idSequence);
}

// Fullscreen
const image_dialog = document.getElementById('fullMedia');
const dialog_container = document.getElementById('fullMediaContainer');

async function openFull(elem) {

    try {
        if (elem.requestFullscreen) {
            await elem.requestFullscreen();
        } else {
            elem.showModal();
        }
    } catch (err) {
        elem.showModal();
    }
}

function closeFull() {

    if (document.fullscreenElement) {
        document.exitFullscreen();
    }
    if (image_dialog.open) {
        image_dialog.close();
    }
}

function addFullScreenCallback(el) {
    el.addEventListener('click', () => {
        const img = document.createElement('img');
        img.src = el.src; // assuming full resolution

        dialog_container.innerHTML = ''; // clear old
        dialog_container.appendChild(img);
        openFull(image_dialog);
    });
}

// Close on Esc or mobile back gesture
image_dialog.addEventListener('cancel', closeFull);       // mobile back press
document.addEventListener('fullscreenchange', () => {
    if (!document.fullscreenElement) image_dialog.close();
});
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeFull();
});
document.getElementById('fullMediaClose').addEventListener('click', closeFull);