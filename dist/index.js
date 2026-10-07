class User {
    city = "New York";
    email;
    UserId;
    constructor(email, UserId) {
        this.email = email;
        this.UserId = UserId;
    }
    get getCity() {
        return this.city;
    }
    set setcity(city) {
        this.city = city;
    }
}
let user1 = new User("lol@.com", 1);
user1.email = "newemail@.com";
let city1 = user1.getCity;
user1.setcity = "Los Angeles";
let city2 = user1.getCity;
console.log(city1);
console.log(city2);
export {};
