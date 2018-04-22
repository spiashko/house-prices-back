import pickle

import numpy as np
import pandas as pd
from bson.binary import Binary

from houseprices import db
from houseprices.constants import available_trainers
from houseprices.train_service.trainers import train_gb, calc_error, train_linear, train_ridge, train_lasso_lars
from houseprices.utils import fill_na, make_transform, dealing_with_missing_data, get_features_by_type, \
    perform_encoding, get_filtered_features_for_transform, get_added_columns, transform_before_learn, prepare_model


def verify_request(content):
    methods = content['methods']

    methods_df = pd.DataFrame()
    methods_df['name'] = [o['name'] for o in methods]
    methods_df['value'] = [o['value'] for o in methods]

    values_sum = 0
    for index, row in methods_df.iterrows():
        if row['name'] in available_trainers:
            values_sum += row['value']
    assert values_sum == 1


def train_request_preprocessor(df_train_cleaned, content):
    # pre-compute
    fill_na(df_train_cleaned)
    make_transform(df_train_cleaned)

    # filtering
    base_features = content['baseFeatures']
    filtered_base_features = dealing_with_missing_data(df_train_cleaned, base_features)

    features_to_boolean_transform = [o['featureName'] for o in content['toBooleanTransform']]
    filtered_features_to_boolean_transform = dealing_with_missing_data(df_train_cleaned, features_to_boolean_transform)

    # get types
    categorical, numerical_int, numerical_float = get_features_by_type(df_train_cleaned, filtered_base_features)

    # perform_encoding
    dummies = perform_encoding(df_train_cleaned, categorical)

    # start build model
    to_log_transform, to_pow_transform, to_boolean_transform = get_filtered_features_for_transform(
        filtered_base_features, filtered_features_to_boolean_transform, content)

    log_columns, quadratic_columns, boolean_columns = get_added_columns(to_log_transform,
                                                                        to_pow_transform,
                                                                        to_boolean_transform)

    transform_before_learn(df_train_cleaned, to_log_transform, to_pow_transform,
                           to_boolean_transform)

    model_for_client = prepare_model(df_train_cleaned, dummies, numerical_int, numerical_float, categorical,
                                     boolean_columns)

    model_for_client_bytes = pickle.dumps(model_for_client)

    # define full features list
    features_full_list = filtered_base_features + quadratic_columns + log_columns + boolean_columns

    # save stuff for future prediction
    prediction_stuff = {"methods": content['methods'], "features_full_list": features_full_list, "dummies": dummies,
                        "to_log_transform": to_log_transform, "to_pow_transform": to_pow_transform}
    prediction_stuff_bytes = pickle.dumps(prediction_stuff)

    instance_collection = db["instance"]
    instance_collection.replace_one({"objectName": "model_for_client"},
                                    {"objectName": "model_for_client", "value": Binary(model_for_client_bytes)},
                                    upsert=True)
    instance_collection.replace_one({"objectName": "prediction_stuff"},
                                    {"objectName": "prediction_stuff", "value": Binary(prediction_stuff_bytes)},
                                    upsert=True)

    return features_full_list


def train_request_processor(df_train_cleaned, df_train, features_full_list, content):
    # training
    methods = content['methods']

    methods_df = pd.DataFrame()
    methods_df['name'] = [o['name'] for o in methods]
    methods_df['value'] = [o['value'] for o in methods]

    used_trainers = train_methods(methods_df, df_train_cleaned, df_train, features_full_list)

    prediction = np.zeros(len(df_train['SalePrice']))
    for trainer in used_trainers.keys():
        value = float(methods_df.loc[methods_df['name'] == trainer]['value'])
        prediction = prediction + np.expm1(used_trainers[trainer].model.predict(df_train[features_full_list])) * value

    final_error = calc_error(df_train['SalePrice'].values, prediction)

    errors_per_trainer = []
    for trainer in used_trainers.keys():
        errors_per_trainer.append({'name': used_trainers[trainer].name, 'error': float(used_trainers[trainer].error)})

    response_dict = {'finalError': float(final_error), 'errorsPerTrainer': errors_per_trainer}

    return response_dict


def train_methods(methods_df, df_train_cleaned, df_train, features_full_list):
    instance_collection = db["instance"]
    used_trainers = {}
    if "gradientBoosting" in methods_df['name'].tolist():
        trainer = train_gb(df_train_cleaned=df_train_cleaned, df_train=df_train, features_full_list=features_full_list)
        instance_collection.replace_one({"objectName": "gradientBoosting"},
                                        {"objectName": "gradientBoosting", "value": Binary(pickle.dumps(trainer))},
                                        upsert=True)
        used_trainers["gradientBoosting"] = trainer
    if "linear" in methods_df['name'].tolist():
        trainer = train_linear(df_train_cleaned=df_train_cleaned, df_train=df_train,
                               features_full_list=features_full_list)
        instance_collection.replace_one({"objectName": "linear"},
                                        {"objectName": "linear", "value": Binary(pickle.dumps(trainer))},
                                        upsert=True)
        used_trainers["linear"] = trainer
    if "ridge" in methods_df['name'].tolist():
        trainer = train_ridge(df_train_cleaned=df_train_cleaned, df_train=df_train,
                              features_full_list=features_full_list)
        instance_collection.replace_one({"objectName": "ridge"},
                                        {"objectName": "ridge", "value": Binary(pickle.dumps(trainer))},
                                        upsert=True)
        used_trainers["ridge"] = trainer
    if "lasso_lars" in methods_df['name'].tolist():
        trainer = train_lasso_lars(df_train_cleaned=df_train_cleaned, df_train=df_train,
                                   features_full_list=features_full_list)
        instance_collection.replace_one({"objectName": "lasso_lars"},
                                        {"objectName": "lasso_lars", "value": Binary(pickle.dumps(trainer))},
                                        upsert=True)
        used_trainers["lasso_lars"] = trainer
    if "elastic_net" in methods_df['name'].tolist():
        trainer = train_lasso_lars(df_train_cleaned=df_train_cleaned, df_train=df_train,
                                   features_full_list=features_full_list)
        instance_collection.replace_one({"objectName": "elastic_net"},
                                        {"objectName": "elastic_net", "value": Binary(pickle.dumps(trainer))},
                                        upsert=True)
        used_trainers["elastic_net"] = trainer
    return used_trainers