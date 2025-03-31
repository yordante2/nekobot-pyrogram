function toggleMode() {
    const body = document.body;
    const button = document.querySelector('.mode-toggle');
    const rectangulo = document.getElementById('tutorial-container');

    if (body.style.backgroundColor === 'white') {
        body.style.backgroundColor = '#121212'; // Activar modo nocturno
        body.style.color = '#FFFFFF';
        rectangulo.classList.remove('modo-claro');
        button.textContent = 'Modo Claro'; // Cambiar texto del botón
    } else {
        body.style.backgroundColor = 'white'; // Activar modo claro
        body.style.color = '#000000';
        rectangulo.classList.add('modo-claro');
        button.textContent = 'Modo Nocturno'; // Cambiar texto del botón
    }
}

function toggleList() {
    const tutorialList = document.getElementById('tutorial-list');
    tutorialList.classList.toggle('visible'); // Mostrar u ocultar la lista
}
