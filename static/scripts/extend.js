count_extensions = 0;
function handle_extend(){
  let re = new XMLHttpRequest();
  re.open('get', '/query/extend');
  re.send();
  re.onload = () => {
  var red = JSON.parse(re.responseText);
  var start = count_extensions;
  for (let tweet=0;tweet<red.length;tweet++){
     document.getElementById("results").innerHTML +='<div id="results_'+count_extensions.toString()+'">' + red[tweet] + '</div>';
    count_extensions += 1;
  }
    render_extended(start,count_extensions);
  }
}

async function render_extended(start,finish){
  for (let i=start;i<finish;i++){
     await twttr.widgets.load(document.getElementById("results_"+i.toString()));
  }
}