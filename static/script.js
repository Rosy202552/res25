function animacionInicio() {
    const overlay = document.querySelector('.overlay');
    overlay.style.opacity = 0;
    setTimeout(() => {
        overlay.style.transition = "opacity 2s";
        overlay.style.opacity = 1;
    }, 500);
}

