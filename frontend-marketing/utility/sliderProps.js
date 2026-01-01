import SwiperCore from "swiper";
import {
  Autoplay,
  EffectFade,
  Grid,
  Navigation,
  Pagination,
  Parallax,
} from "swiper/modules";
SwiperCore.use([Pagination, Navigation, EffectFade, Autoplay, Grid, Parallax]);
export const sliderProps = {
  testimonials: {
    slidesPerView: 1,
    spaceBetween: 0,
    parallax: true,
    effect: "fade",
    speed: 600,
    pagination: {
      el: ".mil-testi-pagination",
      clickable: true,
    },
    navigation: {
      prevEl: ".mil-testi-prev",
      nextEl: ".mil-testi-next",
    },
  },
  testimonials2: {
    slidesPerView: 1,
    spaceBetween: 30,
    speed: 600,
    pagination: {
      el: ".mil-testi-pagination",
      clickable: true,
    },
    breakpoints: {
      992: {
        slidesPerView: 2,
      },
    },
  },
};
