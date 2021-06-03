
count_extensions = 0;
async function get_html(link,order){
  let re_url = new URL("https://old-likes-search.herokuapp.com/get_tweet_html");
  let param_url = new URL("https://publish.twitter.com/oembed");
  param_url.searchParams.append('url',link);
  param_url.searchParams.append('omit_script','true');
  re_url.searchParams.append("url",param_url.href);
  out = await fetch(re_url.href,{method:"GET"});
  return out.json().then(
    async(res)=>{
      document.getElementById('results').innerHTML += '<div id="result_'+order.toString()+'">'+
       res['html']+ '</div>';
      return twttr.widgets.load(document.getElementById("result_"+order.toString()));

    }
    );
}
function handle_extend(){
  let re_links = new XMLHttpRequest();
  re_links.open('get', '/query/extend');
  re_links.send();
  re_links.onload = async() => {
    let links = JSON.parse(re_links.responseText);
    /*await get_html(links[0],0);
    await get_html(links[1],1);*/
    for(i=1;i<links.length;i++){
      await get_html(links[i],count_extensions);
      count_extensions++;
    }
  }
} 