
count_extensions = 0;
async function render_tweets(id,order){
      document.getElementById('results').innerHTML += '<div id="result_'+order.toString()+'">'+'</div>';
      return twttr.createTweet(document.getElementById("result_"+order.toString()));
}
function handle_extend(){
  let re_ids = new XMLHttpRequest();
  re_ids.open('get', '/query/extend');
  re_ids.send();
  re_ids.onload = async() => {
    let ids = JSON.parse(re_ids.responseText);
    
    for(i=1;i<ids.length;i++){
      await render_tweets(ids[i],count_extensions);
      count_extensions++;
    }
  }
} 