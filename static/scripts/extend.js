count_extensions = 0;
function handle_extend(){
  let re = new XMLHttpRequest();
  re.open('get', '/query/extend');
  re.send();
  re.onload = () => {
  var text = re.responseText;
  document.getElementById("results").innerHTML +='<div id="results_'+toString(count_extensions)+'">' + text + '</div>';
   count_extensions += 1;
    twittr.widgets.load(document.getElementById("results_"+toString(count_extensions)));
  }
}