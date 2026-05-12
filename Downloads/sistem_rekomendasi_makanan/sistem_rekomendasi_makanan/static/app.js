// =========================
// LOADING BUTTON
// =========================

const form = document.querySelector("form");
const button = document.querySelector("button");

form.addEventListener("submit", function(){

    button.innerHTML = "Menganalisis Meal Plan...";
    button.disabled = true;

    button.style.opacity = "0.8";

});


// =========================
// ANIMASI PROGRESS BAR
// =========================

window.addEventListener("load", () => {

    const progressBars = document.querySelectorAll(".progress");

    progressBars.forEach(bar => {

        const target = bar.style.width;

        bar.style.width = "0%";

        setTimeout(() => {

            bar.style.width = target;

        }, 400);

    });

});


// =========================
// SMOOTH SCROLL
// =========================

window.addEventListener("load", () => {

    const result = document.querySelector(".result-section");

    if(result){

        setTimeout(() => {

            result.scrollIntoView({
                behavior:"smooth"
            });

        }, 300);

    }

});


// =========================
// CARD HOVER EFFECT
// =========================

const cards = document.querySelectorAll(".meal-card");

cards.forEach(card => {

    card.addEventListener("mouseenter", () => {

        card.style.transform = "translateY(-8px)";

    });

    card.addEventListener("mouseleave", () => {

        card.style.transform = "translateY(0px)";

    });

});


// =========================
// ANIMASI ANGKA KALORI
// =========================

const angkaKalori = document.querySelectorAll(".info-card h2");

angkaKalori.forEach(item => {

    let text = item.innerText;

    if(text.includes("kcal")){

        let target = parseInt(text);

        let count = 0;

        let interval = setInterval(() => {

            count += Math.ceil(target / 40);

            if(count >= target){

                count = target;

                clearInterval(interval);
            }

            item.innerText = count + " kcal";

        }, 30);

    }

});