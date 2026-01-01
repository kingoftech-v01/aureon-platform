import { PageBanner } from "@/components/Banner";
import PlaxLayout from "@/layouts/PlaxLayout";
const page = () => {
  return (
    <PlaxLayout noFooter>
      <PageBanner pageName="Register" title="Register with Plax:" />
      {/* register form */}
      <div className="mil-blog-list mip-p-0-160">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-5">
              <form>
                <input
                  className="mil-input mil-up mil-mb-15"
                  type="text"
                  placeholder="Full name"
                />
                <input
                  className="mil-input mil-up mil-mb-15"
                  type="email"
                  placeholder="Your e-mail"
                />
                <input
                  className="mil-input mil-up mil-mb-15"
                  type="password"
                  placeholder="Password"
                />
                <input
                  className="mil-input mil-up mil-mb-30"
                  type="password"
                  placeholder="Confirm Password"
                />
                <div className="mil-up mil-mb-30">
                  <button type="submit" className="mil-btn mil-md mil-fw">
                    Create Account
                  </button>
                </div>
                <p className="mil-text-xs mil-text-center mil-soft mil-mb-30">
                  Or Register with:
                </p>
                <div className="mil-up mil-mb-15">
                  <a
                    href="#."
                    className="mil-btn mil-md mil-grey mil-fw mil-mb-30"
                  >
                    Sign up with Google
                  </a>
                </div>
                <p className="mil-text-xs mil-soft">
                  By registering, you agree to our{" "}
                  <a href="#." className="mil-accent">
                    Terms and Conditions
                  </a>
                  . Your information is protected and will never be shared with
                  third parties
                </p>
              </form>
            </div>
          </div>
        </div>
      </div>
      {/* register form end */}
      <div className="mil-space-fix" />
    </PlaxLayout>
  );
};
export default page;
