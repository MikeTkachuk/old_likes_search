function pick_backup(name){
            req = new XMLHttpRequest();
            req.open('get', `backups/${name}`)
            req.onload = () => {
                body = document.getElementById('tweets_div')
                domp = new DOMParser();
                tweets_dom = domp.parseFromString(req.responseText, 'text/html');
                body.innerHTML = tweets_dom.body.innerHTML
                }
            req.send()
        };

function topFunction() {
  document.body.scrollTop = 0;
  document.documentElement.scrollTop = 0;
};

function pauseAll(){
    document.querySelectorAll('video').forEach(vid => vid.pause());
    document.querySelectorAll('.vid').forEach(i =>
      i.contentWindow.document.querySelectorAll('video').forEach(vid => vid.pause()));
};

function scrollTo(){
    var val = document.getElementById("navigate_param").value;
    tweets = document.querySelectorAll(".tweet");
    tweets[Math.floor(val / 100 * tweets.length)].scrollIntoView();
};

function shuffle(array) {
  let currentIndex = array.length,  randomIndex;

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
};

function shuffleTweets(){
    tweets = document.querySelectorAll("#tweets_div .tweet")
    tweets_copy = Array()
    tweets.forEach((t) => {tweets_copy.push(t.outerHTML)})

    shuffled_ids = shuffle(Array.from(Array(tweets_copy.length).keys()))

    tweets.forEach((t) => {t.outerHTML = tweets_copy[shuffled_ids.pop()];})
};