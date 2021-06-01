count_extensions = 0;
function handle_extend(){
  let re = new XMLHttpRequest();
  re.open('get', '/query/extend');
  re.send();
  re.onload = () => {
  var red = JSON.parse(re.responseText);
  render_extended(red);
  }
}

async function render_extended(tweets){
  for (let i=0;i<tweets.length;i++){
    let re  = new XMLHttpRequest();
    let url = new URL('https://publish.twitter.com/oembed');
    url.searchParams.append("url",tweets[i]);
    url.searchParams.append("omit_script","true");
    url = url.href;
    await sub_request_handler(url);
    count_extensions++;
  }
}

async function sub_request_handler(link){
  let re_url = new URL("https://old-likes-search.herokuapp.com/get_tweet_html");
    re_url.searchParams.append("url",link);
    re.open('get',re_url.href);
    re.send();
    re.onload = async () => {
      let red = JSON.parse(re.responseText)["html"];
    document.getElementById("results").innerHTML += 
    '<div id="results_'+count_extensions.toString()+'">'+red+'</div>';
     await twttr.widgets.load(document.getElementById("results_"+count_extensions.toString()));
    }
}