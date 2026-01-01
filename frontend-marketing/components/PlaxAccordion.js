"use client";
import { useState } from "react";

const PlaxAccordion = ({ dark }) => {
  const accordionData = [
    {
      id: 1,
      title: "How can I send money with Plax?",
      desc: "Discover the step-by-step process to make money transfers easily and securely with Plax. <br /> <br /> When I hear the buzz of the little world among the stalks, and grow familiar with the countless indescribable forms of the insects and flies, then I feel the presence of the Almighty, who formed us in his own image, and the breath",
    },
    {
      id: 2,
      title:
        "What security measures does Plax have to protect my transactions?",
      desc: "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Dolore assumenda mollitia magni quisquam incidunt necessitatibus error delectus commodi ad exercitationem, dolorem iusto placeat pariatur et aspernatur totam sapiente similique voluptatem quae sunt iste officia sint laborum eum, eos. Molestias modi aliquam accusamus dolore. Mollitia quod omnis ea fugit rem nesciunt ad provident ratione, culpa ex laudantium, enim sit ut eius.",
    },
    {
      id: 3,
      title: "What is the coverage of the Plax network?",
      desc: "Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Vestibulum tortor quam, feugiat vitae, ultricies eget, tempor sit amet, ante. Donec eu libero sit amet quam egestas semper. Aenean ultricies mi vitae est. Mauris placerat eleifend leo.",
    },
    {
      id: 4,
      title: "How can I contact Plax customer service?",
      desc: "Lorem ipsum dolor sit amet, consectetur adipisicing elit. Repellat quo ullam maiores reiciendis, voluptatibus quae odio, accusamus facere vero consectetur! Omnis nobis voluptatum deserunt maxime, error dolor nulla, perspiciatis assumenda quisquam, fugiat magnam placeat culpa sit reprehenderit nesciunt quis praesentium! Quam ullam tempora quidem, totam autem explicabo alias, obcaecati quaerat earum nisi, asperiores ea perspiciatis iusto neque. Odit molestias voluptatem laboriosam distinctio delectus consequatur, quo nemo nihil, deleniti perspiciatis nisi itaque similique accusantium facilis asperiores dicta veniam voluptatum numquam aliquam!",
    },
  ];
  const [active, setActive] = useState(0);
  return (
    <div className={`mil-accordion`}>
      {accordionData.map((item) => (
        <div
          className={`mil-accordion-group mil-up ${
            active == item.id ? " mil-active" : ""
          }`}
          key={item.id}
        >
          <div
            className={`mil-accordion-menu `}
            onClick={() => setActive(active == item.id ? null : item.id)}
          >
            <h5 className={dark ? "mil-light" : ""}>{item.title}</h5>
            <div className="mil-accordion-icon">
              <i className="fas fa-chevron-up" />
            </div>
          </div>
          <div className="mil-accordion-content">
            <p
              className="mil-text-m mil-soft"
              dangerouslySetInnerHTML={{ __html: item.desc }}
            ></p>
          </div>
        </div>
      ))}
    </div>
  );
};
export default PlaxAccordion;
