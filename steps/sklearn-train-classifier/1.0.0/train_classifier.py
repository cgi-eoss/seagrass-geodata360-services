import json
import os
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import sklearn.base


def train_classifier(training_feature_idxs, cross_validation, model_dir, aux_dir, sample_files):
    samples = []
    ground_truth = []
    training_features = list(map(int, training_feature_idxs.split(' ')))

    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    model_file = Path(model_dir).joinpath("%s_model.joblib" % timestamp)
    aux_file = Path(aux_dir).joinpath("%s_model.json" % timestamp)

    for f in sample_files:
        source_file = np.load(f)

        new_samples = source_file['samples'][:, training_features]
        new_ground_truth = source_file['ground_truth']

        print("Loaded %s samples from %s" % (new_samples.shape, f))
        samples.append(new_samples)
        ground_truth.append(new_ground_truth)

    combined_samples = np.concatenate(samples)
    combined_gt = np.concatenate(ground_truth)

    print("Loaded %s total samples" % combined_samples.shape[0])

    classifier_name = os.getenv('SKLEARN_CLASSIFIER', 'RandomForestClassifier')
    if classifier_name == 'RandomForestClassifier' or classifier_name == '':
        clf, aux = train_random_forest_classifier(cross_validation, combined_samples, combined_gt)
    else:
        sys.exit("Unsupported classifier name: %s" % classifier_name)

    print("Writing serialised model to %s" % model_file)
    joblib.dump(clf, model_file)

    print("Writing model aux file to %s" % aux_file)
    aux['model'] = model_file.name
    aux['inputs'] = [Path(f).name for f in sample_files]
    with open(aux_file, 'w') as f:
        json.dump(aux, f, ensure_ascii=False)


def train_random_forest_classifier(cross_validation, samples, gt):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix

    rng = np.random.RandomState(0)

    if cross_validation == "grid_cv":
        from sklearn.model_selection import GridSearchCV

        # TODO Allow externalised parameter grid
        param_grid = {
            'n_estimators': [10, 25, 50, 100, 150, 200],
            'min_samples_split': [0.2, 0.1, 0.05, 0.01, 0.005, 0.001]
        }

        print("Performing grid-search cross-validation for RandomForestClassifier")
        grid_clf = GridSearchCV(RandomForestClassifier(random_state=rng, bootstrap=False), param_grid, n_jobs=-1,
                                verbose=2)
        grid_clf.fit(samples, gt)
        print("Best prediction of accuracy: %s" % (grid_clf.best_score_ * 100))
        print("Best parameters: %s" % grid_clf.best_params_)

        rf = grid_clf.best_estimator_

        predict = rf.predict(samples)
        report = classification_report(gt, predict, output_dict=True)
        conf_matrix = confusion_matrix(gt, predict, normalize='true')

        return rf, {
            'sklearn_version': sklearn.__version__,
            'classifier': 'sklearn.ensemble.RandomForestClassifier',
            'params': grid_clf.best_params_,
            'rng_seed': 0,
            'feature_importances': rf.feature_importances_.tolist(),
            'classification_report': report,
            'confusion_matrix': conf_matrix.tolist()
        }
    else:
        # TODO Expose other RF parameters
        default_params = {'n_estimators': 100, 'min_samples_split': 0.01}
        rf = RandomForestClassifier(random_state=rng, oob_score=True, n_jobs=-1, **default_params)
        rf.fit(samples, gt)
        print("Random Forest OOB prediction of accuracy: %s" % (rf.oob_score_ * 100))

        predict = rf.predict(samples)
        report = classification_report(gt, predict, output_dict=True)
        conf_matrix = confusion_matrix(gt, predict, normalize='true')

        return rf, {
            'sklearn_version': sklearn.__version__,
            'classifier': 'sklearn.ensemble.RandomForestClassifier',
            'params': default_params,
            'rng_seed': 0,
            'feature_importances': rf.feature_importances_.tolist(),
            'classification_report': report,
            'confusion_matrix': conf_matrix.tolist()
        }


if __name__ == '__main__':
    train_classifier(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
