"use client";
import { sliderProps } from "@/utility/sliderProps";
import { Fragment, useState, useEffect } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
import { marketingApi } from "@/lib/api";

// Quote SVG icon component
const QuoteIcon = ({ className }) => (
  <svg
    width={50}
    height={32}
    viewBox="0 0 50 32"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path
      d="M13.0425 9.59881C13.734 7.27646 15.0099 5.16456 16.7515 3.45982C17.0962 3.11455 17.2958 2.65336 17.31 2.16891C17.3243 1.68445 17.1523 1.2126 16.8285 0.848135L16.6225 0.619235C16.3552 0.313531 15.9908 0.106228 15.5887 0.0311485C15.1866 -0.0439312 14.7706 0.0176452 14.4085 0.205827C-0.299477 8.01918 -0.116489 18.6169 0.0295105 20.4165C0.0195105 20.6139 -0.000488281 20.8112 -0.000488281 21.0085C0.0518962 23.1543 0.724816 25.2405 1.93898 27.0214C3.15314 28.8023 4.85796 30.2037 6.85252 31.0604C8.84709 31.9171 11.0483 32.1935 13.1967 31.8569C15.3452 31.5203 17.3514 30.5848 18.9788 29.1606C20.6063 27.7364 21.7873 25.8829 22.3826 23.8185C22.9779 21.7541 22.9627 19.5648 22.3389 17.5086C21.715 15.4524 20.5085 13.615 18.8614 12.2129C17.2144 10.8108 15.1954 9.90246 13.0425 9.59487V9.59881Z"
      fill="#03A6A6"
    />
    <path
      d="M40.2255 9.59881C40.9171 7.27648 42.193 5.16459 43.9345 3.45982C44.2793 3.11455 44.4788 2.65336 44.4931 2.16891C44.5074 1.68445 44.3353 1.2126 44.0115 0.848135L43.8055 0.619235C43.5382 0.313531 43.1738 0.106228 42.7717 0.0311485C42.3696 -0.0439312 41.9536 0.0176452 41.5915 0.205827C26.8835 8.01918 27.0665 18.6169 27.2115 20.4165C27.2015 20.6139 27.1815 20.8112 27.1815 21.0085C27.2332 23.1544 27.9055 25.241 29.1191 27.0224C30.3328 28.8038 32.0373 30.2057 34.0318 31.063C36.0262 31.9203 38.2274 32.1972 40.3761 31.8611C42.5248 31.525 44.5313 30.5899 46.1591 29.166C47.787 27.742 48.9684 25.8887 49.5641 23.8242C50.1599 21.7598 50.1451 19.5704 49.5215 17.514C48.8979 15.4576 47.6915 13.6199 46.0445 12.2176C44.3975 10.8152 42.3785 9.90659 40.2255 9.59881Z"
      fill="#03A6A6"
    />
  </svg>
);

// Default testimonials (fallback if API fails)
const defaultTestimonials = [
  {
    id: 1,
    content: "Aureon has transformed how we manage contracts and invoices. The automation saves us hours every week and our clients love the professional experience.",
    client_name: "Sarah Johnson",
    client_role: "CEO",
    client_company: "Digital Agency Pro",
    client_photo: null,
  },
  {
    id: 2,
    content: "The payment collection feature is a game-changer. We've reduced our outstanding invoices by 60% since switching to Aureon.",
    client_name: "Michael Chen",
    client_role: "Finance Director",
    client_company: "Tech Solutions Inc",
    client_photo: null,
  },
  {
    id: 3,
    content: "Setting up was incredibly easy, and the customer support team was there every step of the way. Highly recommend for any service business.",
    client_name: "Emily Rodriguez",
    client_role: "Founder",
    client_company: "Creative Studio",
    client_photo: null,
  },
  {
    id: 4,
    content: "The analytics dashboard gives us real-time insights into our cash flow. It's like having a financial advisor built into our workflow.",
    client_name: "David Kim",
    client_role: "Operations Manager",
    client_company: "Consulting Group",
    client_photo: null,
  },
];

const Testimonials1 = () => {
  const [testimonials, setTestimonials] = useState(defaultTestimonials);

  useEffect(() => {
    const fetchTestimonials = async () => {
      try {
        const response = await marketingApi.getTestimonials();
        if (response && response.data && response.data.length > 0) {
          setTestimonials(response.data);
        }
      } catch (error) {
        console.error("Failed to fetch testimonials:", error);
      }
    };
    fetchTestimonials();
  }, []);

  return (
    <Fragment>
      <Swiper
        {...sliderProps.testimonials}
        className="mil-testimonials-1 mil-up"
      >
        {testimonials.map((testimonial, index) => (
          <SwiperSlide className="swiper-slide" key={testimonial.id || index}>
            <blockquote
              className="mil-center"
              data-swiper-parallax={-400}
              data-swiper-parallax-opacity={0}
              data-swiper-parallax-scale="0.8"
            >
              <QuoteIcon className="mil-mb-30 mil-up" />
              <p className="mil-mb-60 mil-up">
                {testimonial.content}
              </p>
              {testimonial.client_photo ? (
                <img
                  src={testimonial.client_photo}
                  alt={testimonial.client_name}
                  className="mil-mb-15 mil-up"
                />
              ) : (
                <div
                  className="mil-mb-15 mil-up"
                  style={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #03A6A6 0%, #667eea 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: 24,
                    fontWeight: 'bold',
                    margin: '0 auto',
                  }}
                >
                  {testimonial.client_name?.charAt(0) || 'A'}
                </div>
              )}
              <h5 className="mil-up">{testimonial.client_name}</h5>
            </blockquote>
          </SwiperSlide>
        ))}
        <div className="mil-slider-nav-1">
          <div className="mil-testi-prev" />
          <div className="mil-testi-next" />
        </div>
      </Swiper>
      <div className="mil-testi-pagination mil-up" />
    </Fragment>
  );
};
export default Testimonials1;

export const Testimonials2 = () => {
  const [testimonials, setTestimonials] = useState(defaultTestimonials);

  useEffect(() => {
    const fetchTestimonials = async () => {
      try {
        const response = await marketingApi.getTestimonials();
        if (response && response.data && response.data.length > 0) {
          setTestimonials(response.data);
        }
      } catch (error) {
        console.error("Failed to fetch testimonials:", error);
      }
    };
    fetchTestimonials();
  }, []);

  return (
    <Fragment>
      <Swiper
        {...sliderProps.testimonials2}
        className="swiper-container mil-testimonials-2 mil-up"
      >
        {testimonials.map((testimonial, index) => (
          <SwiperSlide className="swiper-slide" key={testimonial.id || index}>
            <blockquote className="mil-with-bg">
              <QuoteIcon className="mil-mb-30 mil-up mil-accent" />
              <p className="mil-text-m mil-mb-30 mil-up">
                {testimonial.content}
              </p>
              <div className="mil-customer">
                {testimonial.client_photo ? (
                  <img src={testimonial.client_photo} alt={testimonial.client_name} className="mil-up" />
                ) : (
                  <div
                    className="mil-up"
                    style={{
                      width: 50,
                      height: 50,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #03A6A6 0%, #667eea 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: 18,
                      fontWeight: 'bold',
                    }}
                  >
                    {testimonial.client_name?.charAt(0) || 'A'}
                  </div>
                )}
                <h6 className="mil-up">
                  {testimonial.client_name}
                  {testimonial.client_role && (
                    <span style={{ fontWeight: 'normal', opacity: 0.7 }}>
                      {' - '}{testimonial.client_role}
                      {testimonial.client_company && `, ${testimonial.client_company}`}
                    </span>
                  )}
                </h6>
              </div>
            </blockquote>
          </SwiperSlide>
        ))}
      </Swiper>
      <div className="mil-testi-pagination mil-up" />
    </Fragment>
  );
};
