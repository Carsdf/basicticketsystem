ALTER TABLE NewTickets ADD "is_taken" BOOLEAN NOT NULL DEFAULT 0;
ALTER TABLE TakenTickets ADD "is_finished" BOOLEAN NOT NULL DEFAULT 0;
ALTER TABLE NewTickets ADD COLUMN category_id INTEGER REFERENCES Categories(id);
ALTER TABLE TakenTickets ADD COLUMN category_id INTEGER REFERENCES Categories(id);
ALTER TABLE CompletedTickets ADD COLUMN category_id INTEGER REFERENCES Categories(id);
CREATE TABLE Admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL -- store hashed in production!
);
ALTER TABLE TakenTickets
  ADD COLUMN taken_by INTEGER REFERENCES Admins(id);

ALTER TABLE CompletedTickets
  ADD COLUMN completed_by INTEGER REFERENCES Admins(id);

  