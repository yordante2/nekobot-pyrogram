

function toggleMode() {
    const body = document.body;
    const rectangulo = document.querySelectorAll('.rectangulo');
    const links = document.querySelectorAll('a');
    
    body.classList.toggle('modo-claro');

    // Actualiza los colores dinámicamente
    rectangulo.forEach(element => {
        if (body.classList.contains('modo-claro')) {
            element.classList.add('modo-claro');
        } else {
            element.classList.remove('modo-claro');
        }
    });

    links.forEach(link => {
        if (body.classList.contains('modo-claro')) {
            link.classList.add('modo-claro');
        } else {
            link.classList.remove('modo-claro');
        }
    });
}
