import requests

url = "https://api-football-v1.p.rapidapi.com/v3/standings"

querystring = {"season":"2023","league":"140"}

headers = {
	"X-RapidAPI-Key": "6725ad9bb8mshabb13b81c514cbbp15a980jsnf6a8467b3a41",
	"X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())
