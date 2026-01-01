import { PageBanner } from "@/components/Banner";
import { CallToAction2 } from "@/components/CallToAction";
import PlaxLayout from "@/layouts/PlaxLayout";
const page = () => {
  return (
    <PlaxLayout bg={false}>
      <PageBanner
        pageName="Contact us"
        title="Connect with Us: We are Here to Help You"
      />

      {/* contact */}
      <div className="mil-blog-list mil-p-0-160">
        <div className="container">
          <div className="row justify-content-center">
            <div className="col-xl-9">
              <form>
                <div className="row">
                  <div className="col-md-6 mil-mb-30">
                    <input
                      className="mil-input mil-up"
                      type="text"
                      placeholder="Name"
                      name="name"
                    />
                  </div>
                  <div className="col-md-6 mil-mb-30">
                    <input
                      className="mil-input mil-up"
                      type="email"
                      placeholder="Email"
                      name="email"
                    />
                  </div>
                  <div className="col-xl-12 mil-mb-30">
                    <input
                      className="mil-input mil-up"
                      type="tel"
                      placeholder="Telephone number"
                      name="tel"
                    />
                  </div>
                  <div className="col-xl-12 mil-mb-30 ">
                    <textarea
                      cols={30}
                      rows={10}
                      className="mil-up"
                      placeholder="Message"
                      name="message"
                      defaultValue={""}
                    />
                  </div>
                </div>
                <div className="mil-checkbox-frame mil-mb-30 mil-up">
                  <div className="mil-checkbox">
                    <input
                      type="checkbox"
                      id="checkbox"
                      name="checkmark"
                      defaultChecked=""
                    />
                    <label htmlFor="checkbox" />
                  </div>
                  <p className="mil-text-xs mil-soft">
                    I agree that the data submitted, collected and stored *
                  </p>
                </div>
                <div className="mil-up">
                  <button type="submit" className="mil-btn mil-m">
                    Send Message
                  </button>
                </div>
              </form>
              <div className="alert-success" style={{ display: "none" }}>
                <h5>Thanks, your message is sent successfully.</h5>
              </div>
              <div className="mil-p-160-0">
                <h5 className="mil-mb-30 mil-up">
                  We are available on the following channels:
                </h5>
                <p className="mil-text-m mil-soft mil-mb-10 mil-up">
                  Address: 999 Rue du Cherche-Midi, 7755500666 Paris, France
                </p>
                <p className="mil-text-m mil-soft mil-mb-10 mil-up">
                  Telephone: +001 (808) 555-0111
                </p>
                <p className="mil-text-m mil-soft mil-mb-10 mil-up">
                  Fax: +001 (808) 555-0112
                </p>
                <p className="mil-text-m mil-soft mil-up">
                  Email: support@plax.network
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* contact end */}
      {/* call to action */}
      <CallToAction2 />
      {/* call to action end */}
    </PlaxLayout>
  );
};
export default page;
