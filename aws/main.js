// Init state
let allTweets = {}; // map: id → { id, filenames: [...], metadata: {...} }
let idSequence = [];
const BATCH_SIZE = 20;
let nextIndex = 0;

// Setup observer on the anchor
const observer = new IntersectionObserver(onIntersect, {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
});

const [listResp, metaResp] = await Promise.all([
    fetch("tweets_list_cache.txt"),
    fetch("tweets_metadata_cache.txt")
]);
if (!listResp.ok || !metaResp.ok) {
    throw new Error('Failed to fetch files');
}
const [listText, metaText] = await Promise.all([listResp.text(), metaResp.text()]);
parseListing(listText);
parseJsonLines(metaText);
updateSequence()

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
            id: group,
            filenames,
            metadata: null
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
                allTweets[id] = { id, filenames: [], metadata: obj };
            }
        } catch (err) {
            console.warn('Skipping bad JSON line:', trimmed);
        }
    }
}


// Main sequence generator
function updateSequence(){
    idSequence = [];
    Object.values(allTweets).forEach(tweet => {idSequence.push(tweet.id)});
}


// Render the next batch of items into gallery
function renderBatch() {
    const tweets_div = document.getElementById('tweets_div');
    const slice = idSequence.slice(nextIndex, nextIndex + BATCH_SIZE);
    slice.forEach(item => {
        tweets_div.appendChild(createTweetBlock(allTweets[item].metadata));
    });
    nextIndex += slice.length;
    if (nextIndex >= idSequence.length && observer) {
        console.log("reached end, disconnecting observer...");
        observer.disconnect(); // no more to load
    }
}

// IntersectionObserver callback
function onIntersect(entries) {
    console.log("triggered onIntersect");
    entries.forEach(entry => {
        if (entry.isIntersecting && nextIndex < idSequence.length) {
            renderBatch();
        }
    });
}


// Initialize gallery and observer
function resetView(){
    const tweets_div = document.getElementById('tweets_div');
    tweets_div.innerHTML = '';
    nextIndex = 0;
    renderBatch();
    const anchor = document.getElementById('scroll-anchor');
    observer.observe(anchor);
}

// Renderer
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
        } else {
            mediaEl = document.createElement('video');
            mediaEl.className = 'gif';
            mediaEl.src = mediaUrl;
            mediaEl.autoplay = true;
            mediaEl.loop = true;
            mediaEl.muted = true;
            mediaEl.playsInline = true;
            mediaEl.loading = 'lazy';
        }

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
    document.querySelectorAll('.vid').forEach(i =>
        i.contentWindow.document.querySelectorAll('video').forEach(vid => vid.pause()));
}

export function scrollTo() {
    // todo 
    const val = document.getElementById("navigate_param").value;
    let tweets = document.querySelectorAll(".tweet");
    tweets[Math.floor(val / 100 * tweets.length)].scrollIntoView();
}

function shuffle(array) {
    let currentIndex = array.length, randomIndex;

    // While there remain elements to shuffle.
    while (currentIndex != 0) {

        // Pick a remaining element.
        randomIndex = Math.floor(Math.random() * currentIndex);
        currentIndex--;

        // And swap it with the current element.
        [array[currentIndex], array[randomIndex]] = [
            array[randomIndex], array[currentIndex]];
    }

    return array;
}

export function shuffleTweets() {
    let tweets = document.querySelectorAll("#tweets_div .tweet")
    let tweets_copy = Array()
    tweets.forEach((t) => {
        tweets_copy.push(t.outerHTML)
    })

    let shuffled_ids = shuffle(Array.from(Array(tweets_copy.length).keys()))

    tweets.forEach((t) => {
        t.outerHTML = tweets_copy[shuffled_ids.pop()];
    })
}