function toggleList() {
    const tutorialList = document.getElementById('tutorial-list');
    tutorialList.classList.toggle('visible');
}

function toggleMode() {
    const body = document.body;
    const rectangulos = document.querySelectorAll('.rectangulo');
    const links = document.querySelectorAll('a');
    const button = document.querySelector('.mode-toggle'); // Botón para alternar el texto

    // Verificar si la clase 'modo-claro' está siendo aplicada
    const isLightMode = body.classList.toggle('modo-claro');

    // Cambia dinámicamente las clases de los rectángulos
    rectangulos.forEach(rectangulo => {
        rectangulo.classList.toggle('modo-claro', isLightMode);
    });

    // Cambia dinámicamente las clases de los enlaces
    links.forEach(link => {
        link.classList.toggle('modo-claro', isLightMode);
    });

    // Cambiar el texto del botón basándose en el estado
    button.textContent = isLightMode ? 'Modo Oscuro' : 'Modo Claro';
}
