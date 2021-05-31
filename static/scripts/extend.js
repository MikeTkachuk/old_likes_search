count_extensions = 0;
function handle_extend(){
  let re = new XMLHttpRequest();
  re.open('get', '/query/extend');
  re.send();
  re.onload = () => {
  var text = re.responseText;
  document.getElementById("results").innerHTML +='<div id="results_'+count_extensions.toString()+'">' + text + '</div>';
  
    twttr.widgets.load(document.getElementById("results_"+count_extensions.toString()));
    count_extensions += 1;
  }
}