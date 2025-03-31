function toggleMode() {
    const body = document.body;
    const rectangulos = document.querySelectorAll('.rectangulo');
    const links = document.querySelectorAll('a');

    // Alterna la clase en el cuerpo
    body.classList.toggle('modo-claro');

    // Cambia dinámicamente las clases de los rectángulos
    rectangulos.forEach(rectangulo => {
        if (body.classList.contains('modo-claro')) {
            rectangulo.classList.add('modo-claro');
        } else {
            rectangulo.classList.remove('modo-claro');
        }
    });

    // Cambia dinámicamente las clases de los enlaces
    links.forEach(link => {
        if (body.classList.contains('modo-claro')) {
            link.classList.add('modo-claro');
        } else {
            link.classList.remove('modo-claro');
        }
    });
}

function toggleList() {
    const tutorialList = document.getElementById('tutorial-list');
    tutorialList.classList.toggle('visible');
}
