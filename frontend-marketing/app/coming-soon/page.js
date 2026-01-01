import { Fragment } from "react";
const page = () => {
  return (
    <Fragment>
      <div id="smooth-wrapper" className="mil-wrapper">
        {/* preloader */}
        <div className="mil-preloader">
          <div className="mil-load" />
          <p className="h2 mil-mb-30">
            <span className="mil-light mil-counter" data-number={100}>
              100
            </span>
            <span className="mil-light">%</span>
          </p>
        </div>
        {/* preloader end */}
        {/* scroll progress */}
        <div className="mil-progress-track">
          <div className="mil-progress" />
        </div>
        {/* scroll progress end */}
        {/* back to top */}
        <div className="progress-wrap active-progress" />
        {/* content */}
        <div id="smooth-content">
          {/* banner */}
          <div className="mil-banner mil-banner-inner mil-dissolve">
            <div className="container">
              <div className="row align-items-center justify-content-center">
                <div className="col-xl-8">
                  <div className="mil-banner-text mil-text-center mil-mt-130">
                    <div className="mil-text-m mil-mb-20">Coming Soon</div>
                    <h1 className="mil-mb-60">
                      Exciting innovations are coming soon
                    </h1>
                    <div className="row justify-content-center">
                      <div className="col-xl-9">
                        <form className="mil-subscripe-form">
                          <input
                            className="mil-input"
                            type="email"
                            placeholder="Email"
                          />
                          <button type="submit" className="mil-btn mil-md">
                            Create Account
                          </button>
                        </form>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          {/* banner end */}
        </div>
        {/* content end */}
      </div>
    </Fragment>
  );
};
export default page;
