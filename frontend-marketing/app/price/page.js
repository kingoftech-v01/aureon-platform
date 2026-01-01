"use client";
import { CallToAction2 } from "@/components/CallToAction";
import Pricing from "@/components/Pricing";
import PlaxLayout from "@/layouts/PlaxLayout";
import Link from "next/link";
const page = () => {
  return (
    <PlaxLayout bg={false}>
      {/* banner */}
      <div className="mil-banner mil-banner-inner mil-dissolve">
        <div className="container">
          <div className="row align-items-center justify-content-center">
            <div className="col-xl-8">
              <div className="mil-banner-text mil-text-center">
                <div className="mil-text-m mil-mb-20">Pricing</div>
                <h1 className="mil-mb-60">
                  Transparent, Simple and Adapted to your Needs
                </h1>
                <ul className="mil-breadcrumbs mil-pub-info mil-center">
                  <li>
                    <Link href="home">Home</Link>
                  </li>
                  <li>
                    <Link href="price">Pricing</Link>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* banner end */}
      {/* prices*/}
      <div className="mil-blog-list mil-p-0-130">
        <div className="container">
          <Pricing />
        </div>
      </div>
      {/* prices end */}
      <CallToAction2 />
    </PlaxLayout>
  );
};
export default page;
