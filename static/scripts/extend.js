
count_extensions = 0;
async function render_tweets(id,order){
      document.getElementById('results').innerHTML += '<div id="result_'+order.toString()+'">'+'</div>';
      return twttr.ready((twttr)=>{twttr.widgets.createTweet(id,document.getElementById("result_"+order.toString()),{});});
}
function handle_extend(){
      
    for(i=1;i<ids.length;i++){
      render_tweets(ids[i],count_extensions);
      count_extensions++;
    }
}
 