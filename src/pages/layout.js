import React from "react";
import Seo from "../components/seo";
import { container, blue, green, yellow, red } from "./layout.module.css";

const LayoutPage = () => {
  return (
    <div className={container}>
      <div className={blue} />
      <div className={green} />
      <div className={yellow} />
      <div className={red} />
    </div>
  );
};

export const Head = () => <Seo title="Layout" />;

export default LayoutPage;
