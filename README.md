# SphereLink

SphereLink is a web application for managing organizational events. It allows members to create, view, and manage events, while staff users can oversee and moderate content.

## Team Members
- Matías Martínez
- Tomás Giraldo
- David Bermúdez
- Jhon Anderson Marín

## How to Set Up and Work on This Project

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/matias-martinez-moreno/SphereLink.git
    cd SphereLink
    ```

2.  **Switch to the `development` Branch**
    Always work on feature branches created from `development`.
    ```bash
    git checkout development
    ```
3.  **Create and Activate Virtual Environment**
    ```bash
    python -m venv env
    env\Scripts\activate
    ```
4.  **Install Project Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Set Up the Database**
    ```bash
    python manage.py migrate
    ```

6.  **Create Your Superuser**
    This is your personal admin account for the Django admin panel.
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the Development Server**
    ```bash
    python manage.py runserver
    ```

---
### **Managing Dependencies**

**If you install a new package** (e.g., `pip install pillow`), update the `requirements.txt` file so everyone else gets it too.

```bash
pip freeze > requirements.txt
