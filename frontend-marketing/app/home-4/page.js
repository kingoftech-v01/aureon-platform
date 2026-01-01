"use client";
import PlaxAccordion from "@/components/PlaxAccordion";
import { Pricing2 } from "@/components/Pricing";
import PlaxLayout from "@/layouts/PlaxLayout";
import { sliderProps } from "@/utility/sliderProps";
import Link from "next/link";
import { useEffect } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
const page = () => {
  useEffect(() => {
    document.querySelector("#smooth-wrapper").style.backgroundColor = "#192626";
  }, []);

  return (
    <PlaxLayout dark footer={2}>
      {/* banner */}
      <div className="mil-banner mil-dark-1">
        <div className="mil-radial-g-1" />
        <div className="container">
          <div className="row align-items-center">
            <div className="col-xl-6">
              <div className="mil-banner-text">
                <h1 className="mil-display mil-text-gradient mil-mb-60">
                  Control &amp; balance your{" "}
                  <span className="mil-text-img">
                    <img src="img/home-4/Vector.svg" alt="icon" />
                  </span>
                  finances
                </h1>
                <div className="mil-buttons-frame">
                  <Link
                    href="register"
                    className="mil-btn mil-md mil-add-arrow"
                  >
                    Try demo
                  </Link>
                  <a
                    href="https://www.youtube.com/watch?v=gRhoYxy9Oss"
                    className="mil-btn mil-md mil-transp mil-add-play has-popup-video"
                  >
                    Watch tutorial
                  </a>
                </div>
              </div>
            </div>
            <div className="col-xl-6">
              <div className="mil-banner-img mil-120">
                <img
                  src="img/home-4/1.png"
                  alt="banner"
                  style={{ maxWidth: "105%" }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* banner end */}
      {/* icon boxes */}
      <div className="icon-boxes mil-p-160-130">
        <div className="container">
          <div className="mil-text-center">
            <h2 className="mil-light mil-mb-30 mil-up">
              Discover the Benefits
              <br />
              in your Financial
              <br />
              Control
            </h2>
            <p className="mil-text-l mil-dark-soft mil-mb-60 mil-up">
              Explore the advantages that Plax has to offer <br />
              in the world of personal finance
            </p>
          </div>
          <div className="row align-items-center">
            <div className="col-xl-4 mil-mb-30">
              <div className="mil-icon-box mil-bg-fix mil-center mil-up">
                <img
                  src="img/home-4/icons/1.svg"
                  alt="icon"
                  className="mil-mb-30 mil-up"
                />
                <h5 className="mil-mb-20 mil-light mil-up">
                  Personalized Budgets
                </h5>
                <p className="mil-text-s mil-dark-soft mil-mb-30 mil-up">
                  Create realistic and personalized budgets with Plax, adapted
                  to your financial goals and needs.
                </p>
                <a href="#." className="mil-link mil-accent">
                  View more
                </a>
              </div>
            </div>
            <div className="col-xl-4 mil-mb-30">
              <div className="mil-icon-box mil-with-bg mil-dark mil-center mil-up">
                <img
                  src="img/home-4/icons/2.svg"
                  alt="icon"
                  className="mil-mb-30 mil-up"
                />
                <h5 className="mil-mb-20 mil-light mil-up">Debt Control</h5>
                <p className="mil-text-s mil-dark-soft mil-mb-30 mil-up">
                  Know your debt capacity and effectively manage debt payments,
                  avoiding additional charges.
                </p>
                <a href="#." className="mil-link mil-accent">
                  View more
                </a>
              </div>
            </div>
            <div className="col-xl-4 mil-mb-30">
              <div className="mil-icon-box mil-bg-fix mil-center mil-up">
                <img
                  src="img/home-4/icons/3.svg"
                  alt="icon"
                  className="mil-mb-30 mil-up"
                />
                <h5 className="mil-mb-20 mil-light mil-up">
                  Financial Organization
                </h5>
                <p className="mil-text-s mil-dark-soft mil-mb-30 mil-up">
                  Plax allows you to organize your finances with up to 7
                  sections, giving you a map of how your moves.
                </p>
                <a href="#." className="mil-link mil-accent">
                  View more
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* icon boxes end */}
      {/* features */}
      <div className="mil-features mil-p-0-80">
        <div className="container">
          <div className="row flex-sm-row-reverse justify-content-between align-items-center">
            <div className="col-xl-6 mil-mb-80">
              <h2 className="mil-mb-30 mil-light mil-up">
                Optimize finances for <br />
                balance
              </h2>
              <p className="mil-text-l mil-dark-soft mil-mb-60 mil-up">
                From more precise control of your expenses to <br />
                effective planning of financial goals, gives you <br />
                the necessary tools to achieve successful
              </p>
              <div className="mil-up">
                <Link href="register" className="mil-btn mil-m mil-add-arrow">
                  Learn More
                </Link>
              </div>
            </div>
            <div className="col-xl-5 mil-mb-80">
              <div className="mil-image-frame mil-visible-overflow">
                <img src="img/home-4/2.png" alt="image" className="mil-up" />
                <div className="mil-img-box mil-soft-box mil-up">
                  <img src="img/home-1/icons/4.svg" alt="icon" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* features end */}
      {/* features */}
      <div className="mil-features mil-p-0-80">
        <div className="container">
          <div className="row justify-content-between align-items-center">
            <div className="col-xl-6 mil-mb-80">
              <h2 className="mil-mb-30 mil-light mil-up">
                Smart, simple financial planner.
              </h2>
              <p className="mil-text-l mil-dark-soft mil-mb-60 mil-up">
                Whether you’re looking to plan for retirement, save for your
                child’s education, or invest in your future, we have the
                expertise and tools to help you succeed.
              </p>
              <ul className="mil-list-2 mil-type-2 mil-mb-60">
                <li>
                  <div className="mil-up">
                    <h5 className="mil-light mil-mb-15">
                      Variety of transfer methods
                    </h5>
                  </div>
                </li>
                <li>
                  <div className="mil-up">
                    <h5 className="mil-light mil-mb-15">
                      Multicurrency global account
                    </h5>
                  </div>
                </li>
              </ul>
              <div className="mil-up">
                <Link href="register" className="mil-btn mil-m mil-add-arrow">
                  Learn More
                </Link>
              </div>
            </div>
            <div className="col-xl-5 mil-mb-80">
              <div className="mil-image-frame mil-visible-overflow">
                <img src="img/home-4/3.png" alt="image" className="mil-up" />
                <div className="mil-img-box mil-left-box mil-soft-box mil-up">
                  <img src="img/home-1/icons/4.svg" alt="icon" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* features end */}
      {/* call to action */}
      <div className="mil-cta mil-up">
        <div className="container">
          <div className="mil-out-frame mil-image mil-p-160-160">
            <div className="row flex-sm-row-reverse justify-content-between align-items-center">
              <div className="col-xl-6">
                <h2 className="mil-light mil-mb-30 mil-up">
                  Discover How Plax Works to Transform your Finances
                </h2>
                <p className="mil-text-l mil-dark-soft mil-mb-60 mil-up">
                  From creating budgets to detailed e<br />
                  xpense tracking,
                </p>
                <ul className="mil-list-2 mil-type-2 mil-mb-60">
                  <li>
                    <div className="mil-up">
                      <h5 className="mil-light mil-mb-15">
                        Variety of transfer methods
                      </h5>
                      <p className="mil-text-m mil-dark-soft">
                        Design custom budgets that fit your financial goals and
                        lifestyle.
                      </p>
                    </div>
                  </li>
                  <li>
                    <div className="mil-up">
                      <h5 className="mil-light mil-mb-15">
                        Multicurrency global account
                      </h5>
                      <p className="mil-text-m mil-dark-soft">
                        Identify areas of savings and maximize your capacity to
                        accumulate resources for future goals.
                      </p>
                    </div>
                  </li>
                </ul>
              </div>
              <div className="col-xl-5">
                <div className="mil-image-frame mil-visible-overflow">
                  <img src="img/home-4/4.png" alt="image" className="mil-up" />
                  <div className="mil-img-box mil-soft-box mil-up">
                    <div>
                      <h2 className="mil-mb-15">100%</h2>
                      <p className="mil-text-s">
                        Security in your <br />
                        payments
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* call to action end */}
      {/* prices*/}
      <div className="mil-blog-list mil-p-160-130">
        <div className="container">
          <div className="mil-text-center">
            <h2 className="mil-light mil-mb-30 mil-up">
              Choose your Plan and <br />
              Transform your <br />
              Finances
            </h2>
            <p className="mil-text-l mil-dark-soft mil-mb-60 mil-up">
              Plax has the perfect plan to help you achieve your <br />
              financial goals.
            </p>
          </div>
          <Pricing2 />
        </div>
      </div>
      {/* prices end */}
      {/* call to action */}
      <div className="mil-cta mil-p-0-160 mil-up">
        <div className="container">
          <div className="mil-out-frame mil-bg-1">
            <div className="row justify-content-center align-items-center mil-p-160-160">
              <div className="col-xl-7 mil-text-center">
                <h2 className="mil-mb-30 mil-up">
                  Your financial peace of mind is our Total priority
                </h2>
                <p className="mil-text-m mil-soft mil-mb-60 mil-up">
                  At Plax, we understand the importance of the security <br />
                  and privacy of your financial data.
                </p>
                <div className="mil-up">
                  <Link href="about" className="mil-btn mil-md mil-add-arrow">
                    Explore more
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* call to action end */}
      {/* testimonials */}
      <div className="mil-testimonials mil-p-0-160">
        <div className="container">
          <Swiper
            {...sliderProps.testimonials2}
            className="swiper-container mil-testimonials-2 mil-up"
          >
            <SwiperSlide className="swiper-slide">
              <blockquote className="mil-with-bg mil-dark">
                <svg
                  width={50}
                  height={32}
                  viewBox="0 0 50 32"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="mil-mb-30 mil-up mil-accent"
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
                <p className="mil-text-l mil-light mil-mb-30 mil-up">
                  Managing savings has never been so easy. Plax has helped me
                  achieve my financial goals faster than I imagined.
                </p>
                <div className="mil-customer">
                  <img
                    src="img/faces/1.jpg"
                    alt="Customer"
                    className="mil-up"
                  />
                  <h6 className="mil-light mil-up">Rüdiger Karlsen</h6>
                </div>
              </blockquote>
            </SwiperSlide>
            <SwiperSlide className="swiper-slide">
              <blockquote className="mil-with-bg mil-dark">
                <svg
                  width={50}
                  height={32}
                  viewBox="0 0 50 32"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="mil-mb-30 mil-up mil-accent"
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
                <p className="mil-text-l mil-light mil-mb-30 mil-up">
                  Plax's security is unparalleled. I feel comfortable knowing
                  that my data is protected while I control my finances.
                </p>
                <div className="mil-customer">
                  <img
                    src="img/faces/2.jpg"
                    alt="Customer"
                    className="mil-up"
                  />
                  <h6 className="mil-light mil-up">Branka Berg</h6>
                </div>
              </blockquote>
            </SwiperSlide>
            <SwiperSlide className="swiper-slide">
              <blockquote className="mil-with-bg mil-dark">
                <svg
                  width={50}
                  height={32}
                  viewBox="0 0 50 32"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="mil-mb-30 mil-up mil-accent"
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
                <p className="mil-text-l mil-light mil-mb-30 mil-up">
                  Plax adapts to my needs. I can customize my plan and I really
                  feel like I am in control who formed us in his own image.
                </p>
                <div className="mil-customer">
                  <img
                    src="img/faces/3.jpg"
                    alt="Customer"
                    className="mil-up"
                  />
                  <h6 className="mil-light mil-up">Karl Andreassen</h6>
                </div>
              </blockquote>
            </SwiperSlide>
            <SwiperSlide className="swiper-slide">
              <blockquote className="mil-with-bg mil-dark">
                <svg
                  width={50}
                  height={32}
                  viewBox="0 0 50 32"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="mil-mb-30 mil-up mil-accent"
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
                <p className="mil-text-l mil-light mil-mb-30 mil-up">
                  Plax's security is unparalleled. I feel comfortable knowing
                  that my data is protected while I control my finances.
                </p>
                <div className="mil-customer">
                  <img
                    src="img/faces/2.jpg"
                    alt="Customer"
                    className="mil-up"
                  />
                  <h6 className="mil-light mil-up">Bett Nilsen</h6>
                </div>
              </blockquote>
            </SwiperSlide>
          </Swiper>
          <div className="mil-testi-pagination mil-up" />
        </div>
      </div>
      {/* testimonials end */}
      {/* brands */}
      <div className="mil-brands mil-p-0-160">
        <div className="container">
          <h5 className="mil-text-center mil-soft mil-mb-60 mil-up">
            Join over 7,000 satisfied customers who enjoy our service!
          </h5>
          <div className="row justify-content-center">
            <div className="col-6 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/1.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-6 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/2.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-6 col-md-2 mil-text-center">
              <div className="mil-brand">
                <img src="img/brands/3.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-6 col-md-2">
              <div className="mil-brand mil-text-center">
                <img src="img/brands/4.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-6 col-md-2">
              <div className="mil-brand mil-text-center">
                <img src="img/brands/5.svg" alt="brand" className="mil-up" />
              </div>
            </div>
            <div className="col-6 col-md-2">
              <div className="mil-brand mil-text-center">
                <img src="img/brands/6.svg" alt="brand" className="mil-up" />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* brands end */}
      {/* call to action */}
      <div className="mil-cta mil-up">
        <div className="container">
          <div className="mil-out-frame mil-image-2 mil-bg-2">
            <div className="row justify-content-center align-items-center mil-p-160-0">
              <div className="col-xl-7 mil-text-center">
                <h2 className="mil-light mil-mb-30 mil-up">
                  Transform your Financial Future with Plax!
                </h2>
                <p className="mil-text-l mil-light mil-mb-60 mil-up">
                  With our intuitive and personalized tools, achieving your
                  financial goals is within your reach. Invest in your financial
                  success today with Plax!"
                </p>
                <div className="mil-up mil-mb-80">
                  <Link
                    href="register"
                    className="mil-btn mil-md mil-add-arrow"
                  >
                    Try demo
                  </Link>
                </div>
              </div>
              <div className="mil-illustration-absolute mil-type-3 mil-up">
                <img src="img/home-4/5.png" alt="illustration" />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* call to action end */}
      {/* faq */}
      <div className="mil-faq mil-p-160-130">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-8">
              <div className="mil-text-center">
                <h2 className="mil-light mil-mb-30 mil-up">
                  Explore Our Frequently <br />
                  Asked Questions
                </h2>
                <p className="mil-text-l mil-dark-soft mil-mb-60 mil-up">
                  Find quick and clear answers to the most common <br />
                  questions about Plax
                </p>
              </div>
              <PlaxAccordion dark />
            </div>
          </div>
        </div>
      </div>
      {/* faq end */}
    </PlaxLayout>
  );
};
export default page;
