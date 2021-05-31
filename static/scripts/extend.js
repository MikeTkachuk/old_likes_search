count_extensions = 0;
async function handle_extend(){
  let re = new XMLHttpRequest();
  re.open('get', '/query/extend');
  re.send();
  re.onload = () => {
  var red = JSON.parse(re.responseText);
  for (const tweet of red){
     document.getElementById("results").innerHTML +='<div id="results_'+count_extensions.toString()+'">' + red[tweet] + '</div>';
    await twttr.widgets.load(document.getElementById("results_"+count_extensions.toString()));
    count_extensions += 1;
  }
  }
}