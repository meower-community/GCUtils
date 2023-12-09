
// get all the buttons

const buttons = document.querySelectorAll('button');

buttons.forEach((button) => {

    const uuid = button.id;
    button.addEventListener('click', () => {
        // copy to clipboard
        navigator.clipboard.writeText('@gc join ' + uuid);

        window.open(`https://app.meower.org/home/`)
    });
})