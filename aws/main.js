function pick_backup(name){
            req = new XMLHttpRequest();
            req.open('get', `backups/${name}`)
            req.onload = () => {
                body = document.getElementById('tweets_div')
                body.innerHTML = req.responseText
                }
            req.send()
        };