function toggleMode() {
    const body = document.body;
    const rectangulos = document.querySelectorAll('.rectangulo');
    const links = document.querySelectorAll('a');
    const button = document.querySelector('.mode-toggle'); // Botón para alternar el texto

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

    // Cambia el texto del botón
    if (body.classList.contains('modo-claro')) {
        button.textContent = 'Modo Oscuro'; // Texto cuando está en modo claro
    } else {
        button.textContent = 'Modo Claro'; // Texto cuando está en modo oscuro
    }
}
