import { Routes, Route, BrowserRouter} from "react-router-dom"; 
import { Signup } from "../components/pages/Signup";
import { Header } from "../components/templates/Header";
import { StockList } from "../components/pages/StockList";
import { StockDetail } from "../components/pages/StockDetail";

export const Router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Signup />} />
        <Route path="/stocks">
          <Route index element={
            <Header><StockList /></Header>
          } />
          <Route path="detail" element={
            <Header><StockDetail /></Header>
          } />       
        </Route>
      </Routes>
    </BrowserRouter>
  );
};