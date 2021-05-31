function handle_extend(){
  let re = new XMLHttpRequest();
  re.open('get', '/query/extend');
  re.send();
  re.onload = () => {
  var text = re.responseText;
  document.getElementById("results").innerHTML += text;
  }
}