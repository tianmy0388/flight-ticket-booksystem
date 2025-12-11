// 全局动态光影效果（适用于所有页面）
(() => {
    const spotlight = document.getElementById("global-spotlight");
    if (!spotlight) return;
    const update = (evt) => {
        const x = (evt.clientX / window.innerWidth) * 100;
        const y = (evt.clientY / window.innerHeight) * 100;
        spotlight.style.setProperty("--mx", `${x}%`);
        spotlight.style.setProperty("--my", `${y}%`);
    };
    window.addEventListener("mousemove", update);
    window.addEventListener("mouseleave", () => {
        spotlight.style.setProperty("--mx", "50%");
        spotlight.style.setProperty("--my", "50%");
    });
})();
