import styled from "styled-components";
import { useEffect, useState } from 'react';
import { useNavigate, Navigate } from "react-router-dom";
import React from 'react';
import axios from "axios";

const endpoint = "http://localhost:8000/users";

export const Signup = () => {
  const [email, setEmail] = useState("");
  const navigate = useNavigate();
  const onChangeInput = (e : React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
  };

  // idは今のところ仮
  const requestBody = {id: "1", email: email}; 
  const onClickSignUp = () => {
    const emailRegex = /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

    if (!emailRegex.test(email)) {
      alert("正しいメールアドレスの形式で入力してください。");
      return;
    };

    axios.post(endpoint, requestBody).then((res) => {
      if (Object.keys(res.data).length > 0) {
        localStorage.setItem("userID", res.data.ID);
        navigate("/stocks");
      } else {
        alert("登録に失敗しました");  
      }
    }).catch((e) => {
      alert("登録に失敗しました");
    });
  };

  if (localStorage.getItem("userID")) {
    return <Navigate to = "/stocks" />
  }

  return (
    <SWrapper>
      <SContainer>
        <h2 className="title">株価アプリ</h2>
        <p>
          株価アプリは、アカウント登録不要で、気になる銘柄の株価を
          通知できる、デイトレード向けアプリケーションです。通知に使用するメールアドレスを登録して、アプリを始めましょう。
        </p>
        <SInputArea>
          <SInput type="email" placeholder="メールアドレスを入力してください" onChange={onChangeInput} />
          <SButton onClick={onClickSignUp}>始める</SButton>
        </SInputArea>
      </SContainer>
    </SWrapper>
  );
};

const SWrapper = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  width: 100%;
`;

const SContainer = styled.div`
  margin: 100px auto;
  padding: 0 1.5rem 200px;
  max-width: 500px;

  .title {
    text-align: center;  
  }
`;

const SInputArea = styled.div`
  display: flex;
  gap: 8px;
  align-items: center;
`;

const SInput = styled.input`
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #ddd;
  border-radius: 8px;
  outline: none;

  &:focus {
    border-color: #11999e;
  }
`;

const SButton = styled.button`
  background-color: #11999e;
  color: #fff;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: opacity 0.3s;
  &:hover {
    opacity: 0.8;
  }
`;