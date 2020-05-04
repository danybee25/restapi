from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/api', methods=['GET', 'POST'])
def test():
    if request.method == 'POST':
        energy_data = request.get_json()
        load = energy_data['load']  # This is the load energy that should be compensated for by the power stations.
        gas_cost = energy_data['fuels']['gas(euro/MWh)']  # Price of gas calculated in (euro/MWh)
        co2_cost = energy_data['fuels']["co2(euro/ton)"]
        kerosine_cost = energy_data['fuels']['kerosine(euro/MWh)']  # Price of kerosine calculated in (euro/MWh)

        available_power_plants = energy_data['powerplants']

        #calculate unit cost for each plant
        for plant in available_power_plants:

            if "gas" in plant["name"]:
                # cost = (gas_cost / plant["efficiency"])# for no co2
                cost = (gas_cost/plant["efficiency"])+ (0.3*co2_cost)

            elif 'tj' in plant["name"]:
                cost = kerosine_cost/plant["efficiency"]
            elif "wind" in plant["name"]:
                cost = 0
            plant.update({"unit cost":cost})

        ##Power plants sorted by unit cost and pmax
        available_power_plants = sorted(available_power_plants, key=lambda k: (k['unit cost'],k["pmax"]), reverse=False)


        power_needed = []  # A list that contains the needed amount of power. This will store the final energy to be supplied to the load.
        index = 0
        reserve = 0
        for plant in (available_power_plants):

            power =0
            if plant['type'] == 'windturbine':

                if load > (plant["pmax"] * energy_data['fuels']['wind(%)'])/100 :

                    power = round((plant['pmax'] * (energy_data['fuels']['wind(%)'] )/ 100), 2)

                elif load <= plant["pmax"] and energy_data['fuels']['wind(%)']/100 > 0:
                    power = load
                    # else:
                    #     power = round(plant["pmax"] * (energy_data['fuels']['wind(%)'] / 100), 2)

                else:
                    pass
            elif plant['type'] == 'gasfired' :
                if load > plant["pmax"]:
                    power = round(plant['pmax'] , 2)

                else:
                    power = round(load, 2)


            elif plant['type'] == 'turbojet':
                if load > plant["pmax"]:
                    power = round(plant['pmax'] , 2)
                    # load -= power
                else:
                    power = round(load, 2)


            index += 1
            print (plant['name'],power)
            if load > 0 and load >= plant['pmin'] :
                load -= power
                power_needed.append({ "name": plant['name'],"p": power})


            elif load > 0 and load < plant['pmin'] :
                power_needed.append({ "name": plant['name'],"p": 0})

            elif load <= 0:
                print("pow",power)
                if plant['pmin'] > power and power>0:
                    reserve = plant['pmin'] - power
                    power_needed.append({"name": plant['name'], "p": plant['pmin']})
                else:
                    reserve = 0
                    power_needed.append({"name": plant['name'], "p": power})
                break
        print(power_needed)
        if reserve > 0:
            print('reserve',reserve)
            power_needed[-2]['p'] = power_needed[-2]['p'] - reserve

        for i in range(index,len(available_power_plants)):
            power_needed.append({"name": available_power_plants[i]["name"], "p": 0})

        if load > 0:
            print("{} MWH of unssatisfied load, load is too small to use powerplants".format(load))

        return jsonify(power_needed)


if __name__ == '__main__':
    app.run(debug=True)
