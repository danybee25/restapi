from flask import Flask, request, jsonify
import logging
import os

LOG_FORMAT = "%(levelname)s %(asctime)s -%(message)s"

filename ='logs/restapi.log'
directory = os.path.dirname(filename)
if not os.path.exists(directory):
    os.makedirs(directory)

logging.basicConfig(filename=filename, level=logging.DEBUG,
                    format=LOG_FORMAT, filemode="w")
logger = logging.getLogger()

app = Flask(__name__)


@app.route('/api', methods=['GET', 'POST'])
def test():
    """Return a json data with the different power plant to satisfy the load energy."""
    if request.method == 'POST':
        energy_data = request.get_json()
        try:
            load = energy_data['load']  # This is the load energy that should be compensated for by the power stations.
            gas_cost = energy_data['fuels']['gas(euro/MWh)']  # Price of gas calculated in (euro/MWh)
            co2_cost = energy_data['fuels']["co2(euro/ton)"]
            kerosine_cost = energy_data['fuels']['kerosine(euro/MWh)']  # Price of kerosine calculated in (euro/MWh)
            available_power_plants = energy_data['powerplants']
            percentage_wind = energy_data['fuels']['wind(%)']
        


            #calculate unit cost for each plant
            for plant in available_power_plants:
                plant_name = plant["name"]
                cost = 0
                if "gas" in plant_name:
                    # cost = (gas_cost / plant["efficiency"])# for no co2
                    cost = (gas_cost/plant["efficiency"])+ (0.3*co2_cost)

                elif 'tj' in plant_name:
                    cost = kerosine_cost/plant["efficiency"]
                elif "wind" in plant_name:
                    cost = 0
                plant.update({"unit cost": cost})

            ##Power plants sorted by unit cost and pmax
            available_power_plants = sorted(available_power_plants, key=lambda k: (k['unit cost'],k["pmax"]), reverse=False)


            power_needed = []  # A list that contains the needed amount of power. This will store the final energy to be supplied to the load.
            index = 0
            reserve = 0
            for plant in (available_power_plants):

                power =0
                plant_type = plant['type']
                if plant_type == 'windturbine':

                    if load > (plant["pmax"] * percentage_wind)/100:
                        logger.debug("Compute the amount of power to be supplied by the wind turbine")
                        power = round((plant['pmax'] * (percentage_wind)/ 100), 2)

                    elif load <= plant["pmax"] and percentage_wind/100 > 0:
                        power = load
                        logger.info("Amount of power to be supplied by the wind turbine when the load is less than wind power")
                        # else:
                        #     power = round(plant["pmax"] * (energy_data['fuels']['wind(%)'] / 100), 2)

                elif plant_type == 'gasfired' :
                    if load > plant["pmax"]:
                        logger.debug("Computing how much power will be generated from the gas plant.")
                        power = round(plant['pmax'] , 2)

                    else:
                        logger.debug(
                            "Computing how much power will be generated from the gas plant for loads less than the pmax")
                        power = round(load, 2)

                elif plant_type == 'turbojet':
                    if load > plant["pmax"]:
                        logger.debug(
                            "Computing how much power will be generated from the turbojet")
                        power = round(plant['pmax'] , 2)
                        # load -= power
                    else:
                        logger.debug(
                            "Computing how much power will be generated from the turbojet for loads less than the pmax")
                        power = round(load, 2)

                index += 1

                plant_pmin = plant['pmin']
                if load > 0 and load >= plant_pmin :
                    load -= power
                    power_needed.append({ "name": plant_name,"p": power})

                elif load > 0 and load < plant_pmin :
                    power_needed.append({ "name": plant_name,"p": 0})

                elif load <= 0:

                    if plant_pmin > power and power>0:
                        reserve = plant_pmin - power
                        power_needed.append({"name": plant_name, "p": plant_pmin})
                    else:
                        reserve = 0
                        power_needed.append({"name": plant_name, "p": power})
                    break

            if reserve > 0:

                power_needed[-2]['p'] = power_needed[-2]['p'] - reserve

            for i in range(index,len(available_power_plants)):
                power_needed.append({"name": available_power_plants[i]["name"], "p": 0})

            if load > 0:
                print("{} MWH of unssatisfied load, load is too small to use powerplants".format(load))

            return jsonify(power_needed)

        except KeyError as e:
            logger.error(str(e))
            return jsonify("missing key value {}".format(str(e))), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
