import requests
import time

def get_user_data(player_name, player_tag):
    api_url = f"https://api.henrikdev.xyz/valorant/v1/account/{player_name}/{player_tag}"
    response = requests.get(api_url)
    
    return response

def get_puiids(player_name, player_tag):
    response = get_user_data(player_name, player_tag)
    
    if response.status_code == 200:
        data = response.json()
        puuid = data["data"]["puuid"]
        print(f"PUUID for {player_name} #{player_tag}: {puuid}")
        return puuid
    else:
        print("Error:", response.status_code)
        return None
        
def get_player_level(data):
    player_level = data["data"]["account_level"]
    return player_level

def get_player_region(player_name, player_tag):
    response = get_user_data(player_name, player_tag)
    
    if response.status_code == 200:
        data = response.json()
        
        # Return the region
        return data["data"]["region"]
    else:
        print("Error:", response.status_code)
        return None

def region_info(data):
    region_names = {
        "ap": "Asia Pacific",
        "na": "North America",
        "eu": "Europe",
        "br": "Brazil",
        "kr": "Korea",
        "latam": "LATAM"
    }

    region = data["region"]
    
    if region in region_names:
        print(f"Player Region: {region_names[region]}")
    else:
        print(f"Unknown Region: {region}")

def general_player_information(player_name, player_tag):
    response = get_user_data(player_name, player_tag)
    
    if response.status_code == 200:
        data = response.json() 
        print("Player ID (PUUID):", data["data"]["puuid"])
        region_info(data['data'])
              
        player_level = get_player_level(data)
        print("Player Level:", player_level)
    else:
        print("Error:", response.status_code)

def get_last_match(region, puuid):
    # Make the API request
    url = f"https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/{region}/{puuid}?size=1"
    latest_match = requests.get(url).json()

    if 'data' in latest_match and latest_match['data']:
        match_data = latest_match['data'][0]
        match_id = match_data['metadata']['matchid']
        server_name = match_data['metadata']['cluster']
        map_name = match_data['metadata']['map']
        game_mode = match_data['metadata']['mode_id'].capitalize()
        game_length = convert_seconds(match_data['metadata']['game_length'])
        total_rounds = match_data['metadata']['rounds_played']
        winner, red_score, blue_score = rounds_information(match_data)
        
        #Print map information
        print("Map information:")
        print("- Match ID:", match_id)
        print("- Server:", server_name)
        print("- Map name:", map_name)
        print("- Mode:", game_mode)
        print("- Time:", game_length)
        print(f"- Total rounds: {total_rounds} rounds")
        
        # Print winner and scores
        if winner == "DRAW":
            print(f"- Winner: {winner}")
        else:
            print(f"- Winner: {winner}: (RED) {red_score} - {blue_score} (BLUE)")
        
        #Print information for all players
        print("\nAll players:")
        processed_parties = set()
        for player in match_data["players"]["all_players"]:
             
            # Check if the player is in a party
            if 'party_id' in player and player['party_id'] not in processed_parties:
                party_players = get_party_players(match_data['players']['all_players'], player['party_id'])
                
                if len(party_players) > 1:
                    show_party_info(player)
                    print("Party with:")
                    for party_player in party_players:
                        show_party_info(party_player, indent=True)
                    
                    # Add the party_id to the set of processed parties
                    processed_parties.add(player['party_id'])
                else: 
                    show_party_info(player)
                    print("Party with: No party")
                    
        # Check if there are no unique party IDs
        if not processed_parties:
            print("No party (no unique party IDs)")
            
    else:
        print("No match data available")
        
def last_match(region, puuid):
    url = f"https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/{region}/{puuid}?size=1"
    
    for _ in range(3):
        try: 
            response = requests.get(url)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            latest_match = response.json()

            # Check if there is data and players information
            if 'data' in latest_match and latest_match['data']:
                match_data = latest_match['data'][0]
                players = match_data.get('players', {}).get('all_players', [])

                # Find the player with the matching PUUID
                for player in players:
                    if player["puuid"] == puuid:
                        return player.get("currenttier_patched", "Rank not available")
                    # elif player["currenttier_patched"] == "Unrated":
                    #     return "Unranked"
                
                # If the loop completes without returning, the player was not found
                print(f"Player with PUUID {puuid} not found in the match data.")
                return "Player not found in the match data."

            # If there's no data, wait for a while before retrying
            print(f"No match data available. Retrying after 5 seconds.")
            time.sleep(5)

        except Exception as e:
            print(f"Error fetching match data: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying

    print("Unable to fetch match data after retries.")
    return None

def get_current_rank(player_name, player_tag):
    puuid = get_puiids(player_name, player_tag)
    region = get_player_region(player_name, player_tag)
    
    current_rank = last_match(region, puuid)
    
    if current_rank:
        print(f"Current Rank for {player_name} #{player_tag}: {current_rank}")      
    else:
        print(f"No rank information found for {player_name} #{player_tag}.")
    
def rounds_information(match_data):
    red_score = match_data['teams']['red']['rounds_won']
    blue_score = match_data['teams']['blue']['rounds_won']
    
    if red_score == blue_score:
        winning_team = "DRAW"
    elif red_score > blue_score:
        winning_team = "RED"
    elif red_score < blue_score:
        winning_team = "BLUE"
    
    if winning_team == "DRAW":
        print(f"Score: {red_score} - {blue_score}")
    elif winning_team == "RED":
        print(f"Score: {red_score} WINNER - {blue_score}")
    else:
        print(f"Score: {red_score} - {blue_score} WINNER")   
        
    return winning_team, red_score, blue_score
        
def show_party_info(player, indent=False):
    prefix = "\t" if indent else ""
    print(f"{prefix}- Player name: {player['name']} #{player['tag']}")
    print(f"{prefix}- Character: {player['character']}")
    print(f"{prefix}- Stats: {player['stats']['kills']} K, {player['stats']['deaths']} D, {player['stats']['assists']} A")
     
def get_party_players(all_players, party_id):
    # Get all players with the same party_id
    return [player for player in all_players if 'party_id' in player and player['party_id'] == party_id]

def convert_seconds(seconds):
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes} minutes, {seconds} seconds"
    
def print_menu():
    print("\nChoose an options:")
    print("[1] Print Player Information")
    print("[2] Get Player ID (PUUID)")
    print("[3] Get Player Current Rank")
    print("[4] Get Last Match")
    print("[5] Exit")
    
def get_player_input():
    player_name = input("Enter player name: ")
    player_tag = input("Enter player tag: ")
    return player_name, player_tag

def get_last_match_input():
    region = input("Enter region (e.g., ap, na, eu, br, kr, latam): ")
    puuid = input("Enter player PUUID: ")
    print("Region:", region)
    print("PUUID:", puuid)
    return region, puuid

def main():
    while True:
        print_menu()
        
        options = input("Choose the options: ")
        
        if options == "1":
            player_name, player_tag = get_player_input()
            general_player_information(player_name, player_tag)
        elif options == "2":
            player_name, player_tag = get_player_input()
            get_puiids(player_name, player_tag)
        elif options == "3":
            player_name, player_tag = get_player_input()
            get_current_rank(player_name, player_tag)
        elif options == "4":
            region, puuid = get_last_match_input()
            get_last_match(region, puuid)
        elif options == "5":
            print("Exiting program. GG!")
            break
        else:
            print("Invalid options")
            
if __name__ == "__main__":
    main()