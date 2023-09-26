from django.http import HttpResponse
from django.shortcuts import redirect, render
from . utilities import *
import csv
import json
from django.http import JsonResponse
import pandas as pd
from .models import team_data_modes , PlayerInfo
from .resources import PlayerInfoResource
from tablib import Dataset
from django.db import transaction  # Import the 'transaction' module
from django.conf import settings
import os
from django.contrib.admin.views.decorators import staff_member_required

# Create your views here.

def main(request):
    
    return render(request,"index.html")

def teams(request):
    team_mode = team_data_modes.objects.first()
    current_mode = team_mode.mode
    if current_mode == 'db':

        unique_clubs = PlayerInfo.objects.values_list('Club', flat=True).distinct()
        # Convert the QuerySet to a list
        teams_names = list(unique_clubs)

    else:
        teams_csv_path = os.path.join(settings.STATICFILES_DIRS[0], 'assets/data/teams_with_links.csv')
        teams = pd.read_csv(teams_csv_path)
        teams_names = list(teams.name.values)
        
    return render(request,"teams.html",{'teams_names':teams_names})


def team_result(request):
    if request.method == "POST":
        clubs_list = request.POST.getlist("input1[]")

        team_mode = team_data_modes.objects.first()
        current_mode = team_mode.mode

        teams_csv_path = os.path.join(settings.STATICFILES_DIRS[0], 'assets/data/teams_with_links.csv')

        
        if current_mode == 'db':
            try:
                common_players , clubs = get_common_players_db(clubs_list)
                # Convert 'born' column to datetime
            
                # common_players['Born'] = pd.to_datetime(common_players['Born'],format='mixed')
                common_players['Born'] = common_players['Born'].apply(parse_date)
                
                # Sort the DataFrame by the 'born' column in descending order
                common_players = common_players.sort_values(by='Born', ascending=False)
                
                
                
            except Exception as e:
                print(f"An error occurred: {str(e)}")

                return redirect(error_page)
        else:
        # try:
            common_players , clubs = get_common_players_scrape(clubs_list,teams_csv_path)
            # Convert 'born' column to datetime
    
            common_players['Born'] = common_players['Born'].apply(parse_date)

            # Sort the DataFrame by the 'born' column in descending order
            common_players = common_players.sort_values(by='Born', ascending=False)
            
        # except Exception as e:
        #     print(f"An error occurred: {str(e)}")

        #     return redirect(error_page)

        clubs = ", ".join(clubs)
        return render(request,"team_result.html",{'common_players':common_players,'clubs':clubs})
    
    return render(request,"team_result.html")



def players(request):
    players_csv_path = os.path.join(settings.STATICFILES_DIRS[0], 'assets/data/teams_with_links.csv')

    players = pd.read_csv(players_csv_path)
    players_names = list(players.name.values)
    return render(request,"players.html",{'players_names':players_names})




def players_result(request):
    if request.method == "POST":
        players_to_compare = request.POST.getlist("input1[]")
        
        # try:
        result = compare_players(players_to_compare)
        # except:
        #     return redirect(error_page)
          
        return render(request,"player_results.html",{'result':result})
    
    return render(request,"player_results.html")


def csv_upload2(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        csv_file = request.FILES['csv_file']

        # Read and decode the CSV file
        csv_data = csv_file.read().decode('utf-8')
        dataset = Dataset().load(csv_data)

        # Check if the dataset is empty
        if len(dataset) == 0:
            return JsonResponse({'error_message': 'CSV file is empty'})

        # Begin a database transaction
        with transaction.atomic():
            # Clear the existing records in the PlayerInfo table
            PlayerInfo.objects.all().delete()

            # Use the PlayerInfoResource to import the dataset into the database
            player_info_resource = PlayerInfoResource()
            result = player_info_resource.import_data(dataset, dry_run=False)

            if result.has_errors():
                # Handle import errors if any
                errors = result.row_errors()
                return JsonResponse({'error_message': f'CSV data import failed. Errors: {errors}'})
            
        return JsonResponse({'message': 'CSV data successfully inserted.'})
    
    return render(request, 'csv_upload.html')  # Render an HTML page with an upload form


def csv_upload(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        # Read and decode the CSV file
        csv_data = csv_file.read().decode('utf-8')
        dataset = Dataset().load(csv_data)

        # Check if the dataset is empty
        if len(dataset) == 0:
            return JsonResponse({'error_message': 'CSV file is empty'})

        try:
            with transaction.atomic():
                # Clear the existing records in the PlayerInfo table
                PlayerInfo.objects.all().delete()

                # Use the PlayerInfoResource to import the dataset into the database
                player_info_resource = PlayerInfoResource()
                result = player_info_resource.import_data(dataset, dry_run=False)

                if result.has_errors():
                    # Handle import errors if any
                    errors = result.row_errors()
                    return JsonResponse({'error_message': f'CSV data import failed. Errors: {errors}'})

            return JsonResponse({'message': 'CSV data successfully inserted.'})
        except Exception as e:
            # Handle any other exceptions that may occur during the import
            return JsonResponse({'error_message': f'An error occurred: {str(e)}'})

    return render(request, 'csv_upload.html')  # Render an HTML page with an upload form

@staff_member_required
def update_mode(request):
    # Get the first instance of team_data_modes (you might want to add error handling if the table is empty)
    mode_instance = team_data_modes.objects.first()

    if request.method == 'POST':
        # Get the selected mode from the form
        selected_mode = request.POST.get('data-source')

        # Update the mode in the database
        mode_instance.mode = selected_mode
        mode_instance.save()

    return render(request, 'update_mode.html', {'mode_instance': mode_instance})

def error_page(request):

    
    return render(request,"error_page.html")
