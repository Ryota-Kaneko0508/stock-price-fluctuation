import { Link } from "react-router-dom";
import * as React from 'react';
import Paper from "@mui/material/Paper";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TablePagination from "@mui/material/TablePagination";
import TableRow from "@mui/material/TableRow";
import styled from "styled-components";

interface Column {
  id: "tick" | "company" | "price_yesterday" | "price_today" | "diff";
  label: string;
  minWidth?: number;
  align?: "right";

  format?: (value: number) => string;
}

const columns: readonly Column[] = [
  { id: "tick", label: "銘柄", minWidth: 170 },
  { id: "company", label: "社名", minWidth: 100 },
  {
    id: "price_yesterday",
    label: "終値",
    minWidth: 170,
    align: "right",
    format: (value: number) => value.toLocaleString("ja-JP", { style: "currency", currency: "JPY" }),
  },
  {
    id: "price_today",
    label: "株価",
    minWidth: 170,
    align: "right",
    format: (value: number) => value.toLocaleString("ja-JP", { style: "currency", currency: "JPY" }),
  },
  {
    id: "diff",
    label: "差分",
    minWidth: 170,
    align: "right",
    format: (value: number) => 
      (value > 0 ? "+" : "") + value.toLocaleString("ja-JP"),
  },
];

interface Data {
  tick: string;
  company: string;
  price_yesterday: number;
  price_today: number;
  diff: number;
}

function createData(
  tick: string,
  company: string,
  price_yesterday: number,
  price_today: number,
): Data {
  const diff = price_today - price_yesterday;
  return { tick, company, price_yesterday, price_today, diff };
}

const rows = [
  createData("AAPL", "Apple, Inc", 15240, 16980),
  createData("TSLA", "Tesla, Inc", 20123, 19811),
  createData("MSFT", "Micro Sort Inc", 30000, 4000),
];

export const StockList = () => {
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(10);

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  const onClickAdd = () => {
    alert("test");
  };
  
  return (
    <SWrapper>
      <SHeaderContainer>
        <STitle>株価一覧</STitle>
        <SButton onClick={onClickAdd}>+ 追加する</SButton>
      </SHeaderContainer>
      <Paper sx={{ width: "100%", overflow: "hidden" }}>
        <TableContainer sx={{ maxHeight: 440 }}>
          <Table stickyHeader aria-label="sticky table">
            <TableHead>
              <TableRow>
                {columns.map((column) => (
                  <TableCell
                    key={column.id}
                    align={column.align}
                    style={{ minWidth: column.minWidth }}
                  >
                    {column.label}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {rows
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((row) => {
                  return (
                    <TableRow
                      hover
                      role="checkbox"
                      tabIndex={-1}
                      key={row.company}
                    >
                      {columns.map((column) => {
                        const value = row[column.id];

                        let textColor = "inherit";
                        
                        if (column.id === "diff") {
                          if (row.diff > 0) textColor = "green";
                          if (row.diff <= 0) textColor = "red";
                        }
                        return (
                          <TableCell key={column.id} align={column.align} style={{color: textColor}}>
                            {column.format && typeof value === "number"
                              ? column.format(value)
                              : value}
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  );
                })}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[10, 25, 100]}
          component="div"
          count={rows.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
    </SWrapper>
  );
};

const SWrapper = styled.div`
  padding: 24px;
  max-width: 1000px;
  margin: 0 auto;
`;

const SHeaderContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
`;

const STitle = styled.p`
  font-price_today: 20px;
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
