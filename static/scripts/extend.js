count_extensions = 0;
async function set_html(link){
  let re_url = new URL("https://old-likes-search.herokuapp.com/get_tweet_html");
    re_url.searchParams.append("url",link);
    out = await fetch(re_url.href,{method:"GET"});
    return out.json()["html"];
}
function handle_extend(){
  let re_links = new XMLHttpRequest();
  re_links.open('get', '/query/extend');
  re_links.send();
  re_links.onload = async() => {
    document.getElementById('results').innerHTML += await set_html('https://publish.twitter.com/oembed?url=https%3A%2F%2Ftwitter.com%2FRussianMemesLtd%2Fstatus%2F1400026144779517964');
    document.getElementById("results").innerHTML += '<blockquote class="twitter-tweet"><p lang="en" dir="ltr">Tomday you don&#39;t shit <a href="https://t.co/RzPQarCgXe">pic.twitter.com/RzPQarCgXe</a></p>&mdash; Russian Memes United (@RussianMemesLtd) <a href="https://twitter.com/RussianMemesLtd/status/1400026144779517964?ref_src=twsrc%5Etfw">June 2, 2021</a></blockquote>';
  twttr.widgets.load(document.getElementById("results"));
  }
} 