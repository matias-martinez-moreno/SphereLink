# SphereLink

A web application for managing organizational events. It allows members to create, view, and manage events, while staff users can oversee and moderate content.

## Team Members
- Matías Martínez
- Tomás Giraldo
- David Bermúdez
- Jhon Anderson Marín

##  Initial Setup

1.  **Clone Repository**
    ```bash
    git clone https://github.com/matias-martinez-moreno/SphereLink.git
    cd SphereLink
    ```

2.  **Create & Activate Virtual Environment**
    ```bash
    python -m venv env
    
    # On Windows
    env\Scripts\activate
    
    # On macOS/Linux
    source env/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run Database Migrations**
    ```bash
    python manage.py migrate
    ```

5.  **Create Superuser**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Run Server**
    ```bash
    python manage.py runserver
    ```
    The application will run at `http://127.0.0.1:8000/`.

##  Git Workflow

**Flow:** `development` → `feature-branch` → `merge` → `development`

1.  **Sync with `development`**
    ```bash
    git checkout development
    git pull origin development
    ```

2.  **Create Feature Branch**
    ```bash
    git checkout -b feature/your-feature-name
    ```

3.  **Commit Changes**
    ```bash
    # After making changes
    git add .
    git commit -m "feat: Short description of the feature"
    ```

4.  **Sync Branch Before Merging**
    ```bash
    git checkout development
    git pull origin development
    git checkout feature/your-feature-name
    git merge development
    ```
    *(Resolve any conflicts if they appear)*

5.  **Merge into `development`**
    ```bash
    git checkout development
    git merge feature/your-feature-name
    ```

6.  **Push to Remote**
    ```bash
    git push origin development
    ```

7.  **Delete Local Branch (Optional)**
    ```bash
    git branch -d feature/your-feature-name
    ```

## Managing Dependencies

To ensure all team members use the same package versions, follow this process when adding a new dependency.

1.  **Install the New Package**
    ```bash
    pip install new-package-name
    ```

2.  **Update the `requirements.txt` File**
    This command saves all current packages and their exact versions to the file.
    ```bash
    pip freeze > requirements.txt
    ```

3.  **Commit the `requirements.txt` File**
    Add the updated `requirements.txt` file to your commit. This ensures everyone on the team will install the new dependency when they set up the project or pull the latest changes.
