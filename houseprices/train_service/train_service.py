import pickle

import numpy as np
import pandas as pd
from bson.binary import Binary

from houseprices import db
from houseprices.constants import available_trainers
from houseprices.train_service.trainers import GradientBoosting, Linear, Ridge, Lasso, ElasticNet, Trainer
from houseprices.utils import get_features_for_transform, get_added_columns, transform_before_learn, prepare_model


def verify_request(content):
    methods = content['methods']

    methods_df = pd.DataFrame()
    methods_df['name'] = [o['name'] for o in methods]
    methods_df['value'] = [o['value'] for o in methods]

    values_sum = 0
    for index, row in methods_df.iterrows():
        if row['name'] in available_trainers:
            values_sum += row['value']
    if values_sum != 1:
        print("Warning: values_sum != 1")


def train_request_preprocessor(full_frame, content):
    # filtering
    base_features = content['baseFeatures']
    features_to_boolean_transform = [o['featureName'] for o in content['toBooleanTransform']]

    instance_collection = db["instance"]
    dummies = instance_collection.find_one({"objectName": "dummies"})["value"]

    # load all features by types
    categorical = instance_collection.find_one({"objectName": "categorical"})["value"]
    numerical_int = instance_collection.find_one({"objectName": "numerical_int"})["value"]
    numerical_float = instance_collection.find_one({"objectName": "numerical_float"})["value"]

    # apply for current base_features
    categorical = list(set(categorical).intersection(base_features))
    numerical_int = list(set(numerical_int).intersection(base_features))
    numerical_float = list(set(numerical_float).intersection(base_features))

    # start build model
    to_log_transform, to_pow_transform, to_boolean_transform = get_features_for_transform(
        base_features, features_to_boolean_transform, content)

    log_columns, quadratic_columns, boolean_columns = get_added_columns(to_log_transform,
                                                                        to_pow_transform,
                                                                        to_boolean_transform)

    transform_before_learn(full_frame, to_log_transform, to_pow_transform,
                           to_boolean_transform)

    model_for_client = prepare_model(full_frame, dummies, numerical_int, numerical_float, categorical,
                                     boolean_columns)

    # define full features list
    features_full_list = base_features + quadratic_columns + log_columns + boolean_columns

    # save stuff for future prediction
    prediction_stuff = {"methods": content['methods'], "features_full_list": features_full_list,
                        "to_log_transform": to_log_transform, "to_pow_transform": to_pow_transform}

    instance_collection.replace_one({"objectName": "model_for_client"},
                                    {"objectName": "model_for_client", "value": model_for_client},
                                    upsert=True)
    instance_collection.replace_one({"objectName": "prediction_stuff"},
                                    {"objectName": "prediction_stuff", "value": prediction_stuff},
                                    upsert=True)

    return features_full_list


def train_request_processor(df_train, df_test, features_full_list, content):
    # training
    methods = content['methods']

    methods_df = pd.DataFrame()
    methods_df['name'] = [o['name'] for o in methods]
    methods_df['value'] = [o['value'] for o in methods]

    used_trainers = train_methods(methods_df, df_train, df_test, features_full_list)

    prediction = np.zeros(len(df_test['SalePrice']))
    for trainer in used_trainers.keys():
        value = float(methods_df.loc[methods_df['name'] == trainer]['value'])
        prediction = prediction + used_trainers[trainer].predict(df_test[features_full_list]) * value

    final_error = Trainer.calc_error(df_test['SalePrice'].values, prediction)

    errors_per_trainer = []
    for trainer in used_trainers.keys():
        errors_per_trainer.append(
            {'name': used_trainers[trainer].get_name(), 'error': float(used_trainers[trainer].error)})

    response_dict = {'finalError': float(final_error), 'errorsPerTrainer': errors_per_trainer}

    return response_dict


def train_methods(methods_df, df_train, df_test, features_full_list):
    instance_collection = db["instance"]
    used_trainers = {}
    if "linear" in methods_df['name'].tolist():
        trainer = Linear()
        trainer.train(df_train, df_test, features_full_list)
        instance_collection.replace_one({"objectName": "linear"},
                                        {"objectName": "linear", "value": Binary(pickle.dumps(trainer))},
                                        upsert=True)
        used_trainers["linear"] = trainer
    if "lasso" in methods_df['name'].tolist():
        trainer = Lasso()
        trainer.train(df_train, df_test, features_full_list)
        instance_collection.replace_one({"objectName": "lasso"},
                                        {"objectName": "lasso", "value": Binary(pickle.dumps(trainer))},
                                        upsert=True)
        used_trainers["lasso"] = trainer
    if "ridge" in methods_df['name'].tolist():
        trainer = Ridge()
        trainer.train(df_train, df_test, features_full_list)
        instance_collection.replace_one({"objectName": "ridge"},
                                        {"objectName": "ridge", "value": Binary(pickle.dumps(trainer))},
                                        upsert=True)
        used_trainers["ridge"] = trainer
    if "elastic_net" in methods_df['name'].tolist():
        trainer = ElasticNet()
        trainer.train(df_train, df_test, features_full_list)
        instance_collection.replace_one({"objectName": "elastic_net"},
                                        {"objectName": "elastic_net", "value": Binary(pickle.dumps(trainer))},
                                        upsert=True)
        used_trainers["elastic_net"] = trainer
    if "gradientBoosting" in methods_df['name'].tolist():
        trainer = GradientBoosting()
        trainer.train(df_train, df_test, features_full_list)
        instance_collection.replace_one({"objectName": "gradientBoosting"},
                                        {"objectName": "gradientBoosting", "value": Binary(pickle.dumps(trainer))},
                                        upsert=True)
        used_trainers["gradientBoosting"] = trainer
    return used_trainers


def save_admin_model(content):
    instance_collection = db["instance"]
    instance_collection.replace_one({"objectName": "admin_model"},
                                    {"objectName": "admin_model", "value": content},
                                    upsert=True)
