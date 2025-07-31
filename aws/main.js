// main.js
import {pauseAll, resetView, shuffleSequence, topFunction, updateSequence} from "./module.js";

document.getElementById('search_button')
    .addEventListener('click', () => {
        updateSequence();
        resetView();
    });

document.getElementById('shuffle')
    .addEventListener('click', () => {
        shuffleSequence();
        resetView();
    });
document.getElementById('top')
    .addEventListener('click', () => {
        topFunction();
    });
document.getElementById('video_pause')
    .addEventListener('click', () => {
        pauseAll();
    });
