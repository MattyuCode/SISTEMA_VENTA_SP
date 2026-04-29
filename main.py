from database import init_db
from app import LibreriaApp

if __name__ == "__main__":
    init_db()
    app = LibreriaApp()
    app.mainloop()