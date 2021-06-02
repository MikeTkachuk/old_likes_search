count_extensions = 0;
function handle_extend(){
  let re_links = new XMLHttpRequest();
  re_links.open('get', '/query/extend');
  re_links.send();
  re_links.onload = () => {
  var red = JSON.parse(re_links.responseText);
  render_extended(red);
  }
} 

async function render_extended(tweets){
  for (let i=0;i<tweets.length;i++){
    let url = new URL('https://publish.twitter.com/oembed');
    url.searchParams.append("url",tweets[i]);
    url.searchParams.append("omit_script","true");
    url = url.href;
    sub_request_handler(url,count_extensions);
    count_extensions++;
  }
 await twttr.widgets.load(document.getElementById('results'));
 
}

function sub_request_handler(link,order){
  let re_url = new URL("https://old-likes-search.herokuapp.com/get_tweet_html");
    re_url.searchParams.append("url",link);
    let re_html  = new XMLHttpRequest();
    re_html.open('get',re_url.href);
    re_html.send();
    re_html.onload = () => {
      let red = JSON.parse(re_html.responseText)["html"];
      set_div(order,red);
    }
}

function set_div(order,content){
document.getElementById("results").innerHTML += content;
    console.log("added div with id 'results_'"+order.toString());
      
}

async function render_tweet(order){
 await twttr.widgets.load(document.getElementById("results_"+order.toString()));  
 console.log("loaded tweet "+order.toString());
} 