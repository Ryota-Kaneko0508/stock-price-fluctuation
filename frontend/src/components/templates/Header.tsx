import styled from "styled-components";
import { Link } from "react-router-dom";
import { ReactNode, FC } from "react";

type Props = {
  children: ReactNode;
};

export const Header: FC<Props> = (props) => {
  const { children } = props;
  return (
    <>
      <SHeader>
        <SLink to="/">株価アプリ</SLink>
      </SHeader>
      {children}
    </>
  );
};

const SHeader = styled.header`
  background-color: #11999e;
  font-size: 1.25rem;
  font-weight: bold;
  padding: 20px 0;
`;

const SLink = styled(Link)`
  color: #fff;
  margin-left: 20px;
  text-decoration: none;
`;