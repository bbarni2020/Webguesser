# Webguesser

Webguesser is a fun and challenging online game where players have to guess the names and dates of websites. Test your web history knowledge with this unique guessing challenge!


## Usage & Deployment

The website is published at [webguesser.masterbros.dev](https://webguesser.masterbros.dev) and the API is accessible at [api-webguesser.masterbros.dev](https://api-webguesser.masterbros.dev).

## Files

- index.html: The homepage where the game starts.
- login.html: The login and registration page.
- dashboard.html: The main game page.
- profile.html: The user profile page.
- loading.html: Loading animation page.
- style.css: The project's stylesheet.
- API.py: The Flask-based API that handles game and user profile operations.
- bot.py: The Discord bot that handles user profile locking and unlocking.
- create.py: Script to create the main database.
- ban_create.py: Script to create the `ban.db` database.
- launcher.py: Script to launch the API and the bot.

## API Endpoints & [Documentation](https://webguesser.masterbros.dev/API/)

### GET /match_new
- Description: Creates a new match for the user if it does not already exist.
- Parameters: `uid` (required) - User ID
- Response: Returns the match details or an error message.

### GET /update_match
- Description: Updates the match details for the user.
- Parameters: `uid` (required) - User ID, `points` (required) - Points scored, `round` (required) - Current round
- Response: Returns the updated match details or an error message.

### POST /update_profile
- Description: Updates the user's profile details.
- Parameters: `uid` (required) - User ID, `leaderboard` (required) - Leaderboard status (1 or 0), `username` (required) - Username, `description` (required) - Description
- Response: Returns a success message or an error message.

### GET /get_profile
- Description: Retrieves the user's profile details.
- Parameters: `uid` (required) - User ID
- Response: Returns the user's profile details or an error message.

### GET /user
- Description: Retrieves the user's public information.
- Parameters: `username` (required) - Username
- Response: Returns the user's public information or an error message.

### GET /is_active
- Description: Checks if the user is active.
- Parameters: `uid` (required) - User ID
- Response: Returns the user's active status or an error message.

### POST /unlock
- Description: Unlocks or locks the user's profile. Requires an API key.
- Headers: `Authorization` (required) - Bearer API key
- Parameters: `uid` (required) - User ID, `active` (required) - Active status (1 or 0)
- Response: Returns a success message or an error message.

## Contribution

If you would like to contribute to the project, please open a pull request or report an issue on the GitHub repository.

## License


I used AI for comment and README English grammar correction and I use AI to clean up and format my code for better readability.
This project is licensed under special license. For more details, see the LICENSE file.

---

Created by: [bbarni2020](https://github.com/bbarni2020)
