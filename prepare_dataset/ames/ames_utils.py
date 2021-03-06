import pandas as pd


def fill_na(frame):
    """
    Transform some numerical features to categorical and some categorical to numerical.
    :type frame: pd.DataFrame
    :param frame:
    """

    # Alley : data description says NA means "no alley access"
    frame["Alley"].fillna("None", inplace=True)
    # BedroomAbvGr : NA most likely means 0
    frame["BedroomAbvGr"].fillna(0, inplace=True)
    # BsmtQual etc : data description says NA for basement features is "no basement"
    frame["BsmtQual"].fillna("No", inplace=True)
    frame["BsmtCond"].fillna("No", inplace=True)
    frame["BsmtExposure"].fillna("No", inplace=True)
    frame["BsmtFinType1"].fillna("No", inplace=True)
    frame["BsmtFinType2"].fillna("No", inplace=True)
    frame["BsmtFullBath"].fillna(0, inplace=True)
    frame["BsmtHalfBath"].fillna(0, inplace=True)
    frame["BsmtUnfSF"].fillna(0, inplace=True)
    # CentralAir : NA most likely means No
    frame["CentralAir"].fillna("N", inplace=True)
    # Condition : NA most likely means Normal
    frame["Condition1"].fillna("Norm", inplace=True)
    frame["Condition2"].fillna("Norm", inplace=True)
    # EnclosedPorch : NA most likely means no enclosed porch
    frame["EnclosedPorch"].fillna(0, inplace=True)
    # External stuff : NA most likely means average
    frame["ExterCond"].fillna("TA", inplace=True)
    frame["ExterQual"].fillna("TA", inplace=True)
    # Fence : data description says NA means "no fence"
    frame["Fence"].fillna("No", inplace=True)
    # FireplaceQu : data description says NA means "no fireplace"
    frame["FireplaceQu"].fillna("No", inplace=True)
    frame["Fireplaces"].fillna(0, inplace=True)
    # Functional : data description says NA means typical
    frame["Functional"].fillna("Typ", inplace=True)
    # GarageType etc : data description says NA for garage features is "no garage"
    frame["GarageType"].fillna("No", inplace=True)
    frame["GarageFinish"].fillna("No", inplace=True)
    frame["GarageQual"].fillna("No", inplace=True)
    frame["GarageCond"].fillna("No", inplace=True)
    frame["GarageArea"].fillna(0, inplace=True)
    frame["GarageCars"].fillna(0, inplace=True)
    # HalfBath : NA most likely means no half baths above grade
    frame["HalfBath"].fillna(0, inplace=True)
    # HeatingQC : NA most likely means typical
    frame["HeatingQC"].fillna("TA", inplace=True)
    # KitchenAbvGr : NA most likely means 0
    frame["KitchenAbvGr"].fillna(0, inplace=True)
    # KitchenQual : NA most likely means typical
    frame["KitchenQual"].fillna("TA", inplace=True)
    # LotFrontage : NA most likely means no lot frontage
    frame["LotFrontage"].fillna(0, inplace=True)
    # LotShape : NA most likely means regular
    frame["LotShape"].fillna("Reg", inplace=True)
    # MasVnrType : NA most likely means no veneer
    frame["MasVnrType"].fillna("None", inplace=True)
    frame["MasVnrArea"].fillna(0, inplace=True)
    # MiscFeature : data description says NA means "no misc feature"
    frame["MiscFeature"].fillna("No", inplace=True)
    frame["MiscVal"].fillna(0, inplace=True)
    # OpenPorchSF : NA most likely means no open porch
    frame["OpenPorchSF"].fillna(0, inplace=True)
    # PavedDrive : NA most likely means not paved
    frame["PavedDrive"].fillna("N", inplace=True)
    # PoolQC : data description says NA means "no pool"
    frame["PoolQC"].fillna("No", inplace=True)
    frame["PoolArea"].fillna(0, inplace=True)
    # SaleCondition : NA most likely means normal sale
    frame["SaleCondition"].fillna("Normal", inplace=True)
    # ScreenPorch : NA most likely means no screen porch
    frame["ScreenPorch"].fillna(0, inplace=True)
    # TotRmsAbvGrd : NA most likely means 0
    frame["TotRmsAbvGrd"].fillna(0, inplace=True)
    # Utilities : NA most likely means all public utilities
    frame["Utilities"].fillna("AllPub", inplace=True)
    # WoodDeckSF : NA most likely means no wood deck
    frame["WoodDeckSF"].fillna(0, inplace=True)


def make_transform(frame):
    """
    Transform some numerical features to categorical.
    :type frame: pd.DataFrame
    :param frame:
    """
    # Some numerical features are actually really categories
    frame.replace(
        {
            "MSSubClass": {20: "SC20", 30: "SC30", 40: "SC40", 45: "SC45",
                           50: "SC50", 60: "SC60", 70: "SC70", 75: "SC75",
                           80: "SC80", 85: "SC85", 90: "SC90", 120: "SC120",
                           150: "SC150", 160: "SC160", 180: "SC180", 190: "SC190"},
            "MoSold": {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                       7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
        },
        inplace=True
    )


def update_dots(frame):
    """
    :type frame: pd.DataFrame
    :param frame:
    """
    frame.replace(
        {
            "HouseStyle": {"1.5Fin": "1_5Fin", "1.5Unf": "1_5Unf", "2.5Fin": "2_5Fin", "2.5Unf": "2_5Unf"}
        },
        inplace=True
    )


def rename_columns(frame):
    """
    Remove whitespaces in column names.
    :type frame: pd.DataFrame
    :param frame:
    """
    columns = frame.columns
    new_names = [column.replace(" ", "").replace("/", "") for column in columns]
    frame.rename(index=str, columns=dict(zip(columns, new_names)), inplace=True)


def dealing_with_missing_data(frame):
    """

    :rtype: list
    :type frame: pd.DataFrame
    :param frame:
    :return: list of applicable features
    """

    # missing data
    total = frame.isnull().sum().sort_values(ascending=False)
    percent = (frame.isnull().sum() / frame.isnull().count()).sort_values(ascending=False)
    missing_data = pd.concat([total, percent], axis=1, keys=['Total', 'Percent'])
    print(missing_data.head(10))

    # remove features where data is missed more then 5 times
    features = (missing_data[missing_data['Total'] > 5]).index.tolist()
    print("features to remove: ")
    print(features)

    frame.drop(columns=features, inplace=True)

    # remove left images where data is missed
    frame.drop(frame.loc[frame.isnull().any(axis=1)].index, inplace=True)
    assert frame.isnull().sum().max() == 0  # just checking that there's no missing data missing...
