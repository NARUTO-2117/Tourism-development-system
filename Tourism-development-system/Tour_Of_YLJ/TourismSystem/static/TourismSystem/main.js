document.addEventListener('DOMContentLoaded', function() {
    // 这里可以放置一些全局的初始化代码
    console.log("Main script loaded.");
});

// 其他通用功能
function showAlert(message) {
    alert(message);
}

//导航栏交互  通用脚本 后续新增功能时，可以参考（全局初始化、网站主要功能交互...)
const navLinks = document.querySelectorAll('.top_nav ul li a');
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const target = link.getAttribute('href');
    });
});
