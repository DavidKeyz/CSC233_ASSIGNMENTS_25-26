#include <iostream>
using namespace std;

int main()
{
    int user_input, positives = 0, negatives = 0, counter = 0, sum = 0;
    double average;

    cout << "Enter an integer, the input ends if it is 0: ";

    while (true)
    {
        cin >> user_input;
        ++counter;
        if (user_input == 0)
            break;
        else if (user_input < 0)
            ++negatives;
        else if (user_input > 0)
            ++positives;
        sum += user_input;
    }

    if (counter == 1)
        cout << "\nNo numbers are entered except 0" << endl;
    else
    {
        average = static_cast<double>(sum) / (counter - 1);
        cout << "The number of positives is " << positives << endl;
        cout << "The number of negatives is " << negatives << endl;
        cout << "The total is " << counter << endl;
        cout << "The average is " << average << endl;
    }

    return 0;
}
